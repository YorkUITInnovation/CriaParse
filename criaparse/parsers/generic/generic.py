import functools
import io
import os
from typing import List

from CriadexSDK.routers.models.azure import ModelAboutRoute
from SemanticDocumentParser import SemanticDocumentParser
from SemanticDocumentParser.llama_extensions.node_parser import AsyncSemanticSplitterNodeParser
from SemanticDocumentParser.utils import with_timings_sync
from fastapi import UploadFile
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.multi_modal_llms.azure_openai import AzureOpenAIMultiModal

from criaparse.daemon.job import Job
from criaparse.models import ElementType, Element, ParserResponse, Asset, FileUnsupportedParseError, ParserFile, ParserStrategy
from criaparse.parser import Parser
from criaparse.parsers import alsyllabus
from criaparse.parsers.generic.errors import ParseModelMissingError

semantic_step_map: dict[str, int] = {
    'Unstructured Partition': 1,
    'Metadata Parsing': 2,
    'Table Parsing 1/2': 3,
    'List Parsing': 4,
    'Paragraph Parsing': 5,
    'Table Parsing 2/2': 6,
    'Image Captioning': 7,
    'Window Combination': 8,
    'Remove Small Nodes': 9
}

semantic_step_map_inverted: dict[int, str] = {v: k for k, v in semantic_step_map.items()}
DOCX_FILETYPE: str = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
AL_EXT_STEP_NAME: str = 'Al Extension'


class GenericParser(Parser):
    """
    Default parser
    """

    @classmethod
    def step_count(cls, **kwargs) -> int:
        extra_steps: int = 0

        if kwargs.get('al_extension') is True:
            extra_steps += 1

        return len(semantic_step_map) + extra_steps

    @classmethod
    def strategy(cls) -> str:
        return ParserStrategy.GENERIC

    def supports_file(self, file: UploadFile) -> bool:
        """
        Override method to support/allow all files
        :param file: The file
        :return: Always supporte
        """

        return True

    def accepted_mimetypes(self) -> List[str]:
        """
        Empty list of accepted mimetypes (all)
        :return: List of allowed mimetypes

        """

        return []

    @classmethod
    async def _set_initial_steps(cls, job: Job, al_extension: bool):
        step_map: dict[int, str] = semantic_step_map_inverted.copy()

        if al_extension:
            step_map[len(semantic_step_map) + 1] = AL_EXT_STEP_NAME

        await job.set_steps(steps=step_map)

    async def _parse(
            self,
            file: ParserFile,
            job: Job,
            **kwargs
    ) -> ParserResponse:
        """
        Use the unstructured API to parse files

        :param file: The file to parse
        :return:

        """

        # Check if ext enabled
        al_extension: bool = bool(kwargs.get('al_extension', False))

        if al_extension and file.content_type != DOCX_FILETYPE:
            raise FileUnsupportedParseError(
                f"The {self.name()} parser's '{AL_EXT_STEP_NAME}' module requires a DOCX file, but you uploaded a {file.content_type.split('/')[-1].upper()}."
            )

        # Update the initial # of steps
        await self._set_initial_steps(job, al_extension)

        llm_model_info: ModelAboutRoute.Response = kwargs['llm_model_info']
        embedding_model_info: ModelAboutRoute.Response = kwargs['embedding_model_info']

        # Must be provided for this parser
        if llm_model_info is None or embedding_model_info is None:
            raise ParseModelMissingError("LLM and embedding model IDs must be provided")

        # Build the LLM Model
        _llm_model = AzureOpenAIMultiModal(
            model=llm_model_info.model.api_model,
            api_key=llm_model_info.model.api_key,
            api_version=llm_model_info.model.api_version,
            azure_endpoint=f"https://{llm_model_info.model.api_resource}.openai.azure.com",
            azure_deployment=llm_model_info.model.api_deployment,
            max_new_tokens=2048
        )

        # Build the node parser
        _node_parser = AsyncSemanticSplitterNodeParser(
            buffer_size=2,
            breakpoint_percentile_threshold=85,
            embed_model=AzureOpenAIEmbedding(
                model=embedding_model_info.model.api_model,
                api_key=embedding_model_info.model.api_key,
                api_version=embedding_model_info.model.api_version,
                azure_endpoint=f"https://{embedding_model_info.model.api_resource}.openai.azure.com",
                azure_deployment=embedding_model_info.model.api_deployment,
            ),
        )

        parser: SemanticDocumentParser = SemanticDocumentParser(
            llm_model=_llm_model,
            node_parser=_node_parser,
        )

        # Function to update the job after each step
        async def on_step_finished(step_name: str, parse_time: float) -> None:
            step_num = semantic_step_map[step_name]
            await job.set_step_finished(step_name=step_name, step_number=step_num, time_taken=parse_time)

        # Parse using the SemanticDocumentParser
        parsed_elements, parser_timings = await parser.aparse(
            document=file.buffer,
            document_filename=file.filename,
            on_step_finished=on_step_finished
        )

        # If al is enabled, parse using that & extend the elements with the extra step
        if al_extension:
            timings, response = with_timings_sync(fn=functools.partial(self.al_extension, file_buffer=file.buffer))
            parsed_elements.extend(response)
            await job.set_step_finished(step_name=AL_EXT_STEP_NAME, step_number=len(semantic_step_map) + 1, time_taken=timings)

        output_elements, output_assets = self.parse_parser_outputs(parsed_elements)

        # Feb 5, 2025, Patrick is away. To add immediate support for assets,
        # I have added 'ENABLE_BACKWARDS_COMPATIBLE_ASSET_CONTAINER' as a TEMPORARY << read: TEMPORARY!!!! solution.
        # This passed an additional 'meta' element Criadex extracts when uploading a document.
        if os.getenv('ENABLE_BACKWARDS_COMPATIBLE_ASSET_CONTAINER', 'false').lower() == 'true':
            output_elements.append(
                Element(
                    type=ElementType.BACKWARDS_COMPATIBLE_ASSET_CONTAINER,
                    text="Backwards Compatible Asset Container",
                    metadata={
                        'assets': [asset.model_dump() for asset in (output_assets or [])]
                    }
                )
            )

            # To prevent duplicate data, since assets are already heavy, if this feature is enabled, assets are excluded from the response.
            output_assets = []

        return ParserResponse(elements=output_elements, assets=output_assets, timings=parser_timings)

    @classmethod
    def al_extension(cls, file_buffer: io.BytesIO) -> List[dict]:
        """Execute the Al extension to extend the generic parser to handle syllabi matching the Al Syllabus template format"""
        return alsyllabus.convert_file_partial(file_buffer)

    @classmethod
    def parse_raw_description(cls, description: str) -> str:
        """
        Extract just the raw description without LLM hint tags

        f"[IMAGE {element['element_id']} DESCRIPTION START]{response.text}[IMAGE {element['element_id']} DESCRIPTION END]"

        :param description: The description to parse (looks like ^^)
        :return: The raw description (response.text in the string above ^^)

        """

        try:
            return description.split('START]')[1].split('[IMAGE')[0]
        except IndexError:
            return description

    @classmethod
    def parse_parser_outputs(cls, elements: List[dict]) -> tuple[List[Element], List[Asset]]:
        """
        Parse the elements & separate assets out for Criadex

        :param elements: Elements to output as serialized elements
        :return: Serialized representation of elements split from assets

        """

        output_elements = []
        output_assets = []

        for element in elements:
            if element['type'] == ElementType.IMAGE.value:
                asset: Asset = Asset(
                    uuid=element['element_id'],
                    data_mimetype=element['metadata'].pop('image_mime_type', None),
                    data_base64=element['metadata'].pop('image_base64', None),
                    description=cls.parse_raw_description(element['text'])
                )

                output_assets.append(asset)
                element['metadata']['asset_uuid'] = element['element_id']

            output_elements.append(
                Element(
                    text=element['text'],
                    metadata=element['metadata'],
                    type=ElementType.of(element['type']),
                )
            )

        return output_elements, output_assets
