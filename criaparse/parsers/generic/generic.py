from typing import List

from CriadexSDK.routers.models.azure import ModelAboutRoute
from SemanticDocumentParser import SemanticDocumentParser
from SemanticDocumentParser.llama_extensions.node_parser import AsyncSemanticSplitterNodeParser
from fastapi import UploadFile
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.multi_modal_llms.azure_openai import AzureOpenAIMultiModal

from criaparse.daemon.job import Job
from criaparse.models import ElementType, Element, ParserResponse, Asset
from criaparse.parser import Parser
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
    'Remove Small Nodes': 9,
}


class GenericParser(Parser):
    """
    Default parser
    """

    @classmethod
    def step_count(cls) -> int:
        return 6

    @classmethod
    def name(cls) -> str:
        return "GENERIC"

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

    async def _parse(
            self,
            file: UploadFile,
            job: Job,
            **kwargs
    ) -> ParserResponse:
        """
        Use the unstructured API to parse files

        :param file: The file to parse
        :return:

        """

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

        async def on_step_finished(step_name: str, parse_time: float) -> None:
            step_num = semantic_step_map[step_name]
            await job.set_step_finished(step_name=step_name, step_number=step_num, time_taken=parse_time)

        parsed_elements, _ = await parser.aparse(
            document=self.to_buffer(file),
            document_filename=file.filename,
            on_step_finished=on_step_finished
        )

        output_elements = []
        output_assets = []

        for element in parsed_elements:

            if element['type'] == ElementType.IMAGE.value:
                asset: Asset = Asset(
                    data_mimetype=element['metadata'].pop('image_mime_type'),
                    data_base64=element['metadata'].pop('image_base64'),
                )

                output_assets.append(
                    asset
                )

                element['metadata']['asset_uuid'] = asset.uuid

            output_elements.append(
                Element(
                    text=element['text'],
                    metadata=element['metadata'],
                    type=ElementType.of(element['type']),
                )
            )

        return ParserResponse(elements=output_elements, assets=output_assets)
