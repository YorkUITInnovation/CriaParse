from typing import List, Optional

from CriadexSDK import CriadexSDK
from CriadexSDK.routers.models.azure import ModelAboutRoute
from SemanticDocumentParser import SemanticDocumentParser
from fastapi import UploadFile
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.azure_openai import AzureOpenAI

from criaparse.parser import Parser, Element, ElementType
from criaparse.parsers.generic.errors import ParseModelMissingError


class GenericParser(Parser):
    """
    Default parser
    """

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

    async def _parse(self, file: UploadFile, **kwargs) -> List[Element]:
        """
        Use the unstructured API to parse files

        :param file: The file to parse
        :return:

        """

        llm_model_id: Optional[int] = kwargs['llm_model_id']
        embedding_model_id: Optional[int] = kwargs['embedding_model_id']
        criadex: CriadexSDK = kwargs['criadex']

        # Must be provided for this parser
        if llm_model_id is None or embedding_model_id is None:
            raise ParseModelMissingError("LLM and embedding model IDs must be provided")

        # Get the model info from Criadex
        llm_model_info: ModelAboutRoute.Response = await criadex.models.azure.about(model_id=llm_model_id)
        embedding_model_info: ModelAboutRoute.Response = await criadex.models.azure.about(model_id=embedding_model_id)

        # Build the LLM Model
        _llm_model = AzureOpenAI(
            model=llm_model_info.model.api_model,
            api_key=llm_model_info.model.api_key,
            api_version=llm_model_info.model.api_version,
            azure_endpoint=f"https://{llm_model_info.model.api_resource}.openai.azure.com",
            azure_deployment=llm_model_info.model.api_deployment,
        )

        # Build the node parser
        _node_parser = SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=80,
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

        parsed_elements, _ = await parser.aparse(
            document=self.to_buffer(file),
            document_filename=file.filename
        )

        output_elements = []

        for element in parsed_elements:
            output_elements.append(
                Element(
                    text=element['text'],
                    metadata=element['metadata'],
                    type=ElementType.of(element['type']),
                )
            )

        return output_elements


