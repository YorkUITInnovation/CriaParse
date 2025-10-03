import functools
import io
import os
from typing import List

from CriadexSDK.routers.models.azure import ModelAboutRoute
from SemanticDocumentParser import SemanticDocumentParser
from SemanticDocumentParser.utils import with_timings_sync
from fastapi import UploadFile
from SemanticDocumentParser.parser import RAGFlow

from criaparse.daemon.job import Job
from criaparse.parser import Parser
from criaparse.models import ElementType, Element, ParserResponse, Asset, FileUnsupportedParseError, ParserFile, ParserStrategy
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

        ragflow_client: RAGFlow = job.criadex.ragflow
        dataset_id: str = kwargs['dataset_id']


        parser: SemanticDocumentParser = SemanticDocumentParser(
            ragflow_client=ragflow_client,
            dataset_id=dataset_id,
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

        # Group elements by top-level H1 sections and extract assets
        if kwargs.get('group_by_h1', True):
            grouped_elements, output_assets = self.group_elements_and_extract_assets(parsed_elements)

            # Convert grouped dicts to Element models, preserving element_id when present
            output_elements: List[Element] = []
            for element in grouped_elements:
                _e = {
                    'text': element.get('text', ''),
                    'metadata': element.get('metadata', {}),
                    'type': ElementType.of(element.get('type', ElementType.NARRATIVE_TEXT.value)),
                }
                eid = element.get('element_id')
                if eid:
                    _e['element_id'] = eid
                output_elements.append(Element(**_e))
        else:
            # Preserve legacy behavior for indexer compatibility
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
                    data_mimetype=element['metadata'].pop('image_mime_type', None) or '',
                    data_base64=element['metadata'].pop('image_base64', None) or '',
                    description=cls.parse_raw_description(element['text'])
                )

                output_assets.append(asset)
                element['metadata']['asset_uuid'] = element['element_id']

            # Preserve the original element_id for linkage
            el_kwargs = dict(
                text=element['text'],
                metadata=element['metadata'],
                type=ElementType.of(element['type']),
            )
            if 'element_id' in element and element['element_id']:
                el_kwargs['element_id'] = element['element_id']
            output_elements.append(Element(**el_kwargs))

        return output_elements, output_assets

    @classmethod
    def group_elements_and_extract_assets(cls, elements: List[dict]) -> tuple[List[dict], List[Asset]]:
        """
        Group parsed elements into semantic sections keyed by H1 (level 1 Title) while extracting assets,
        and preserve per-table and per-image nodes as standalone elements interleaved in order.

        Rules:
        - Maintain one Title section node per H1 that aggregates non-table/ non-image text up to the next H1.
        - Emit Table elements as separate nodes in the output stream at their original positions.
        - Emit Image elements as separate nodes, with metadata.asset_uuid set and caption text preserved.
        - Lower-level titles (H2/H3/...) are included in the current H1 section's text.
        - Preface section is created if content exists before the first H1.
        Returns a tuple of (ordered_nodes_including_sections_tables_images, assets).
        """

        def heading_level(meta: dict) -> int | None:
            if not isinstance(meta, dict):
                return None
            candidates = ['heading_level', 'level', 'title_level', 'header_level']
            for key in candidates:
                val = meta.get(key)
                if val is None:
                    continue
                if isinstance(val, int):
                    return val
                try:
                    sval = str(val).strip()
                    if sval.lower().startswith('h') and len(sval) > 1 and sval[1:].isdigit():
                        return int(sval[1:])
                    if sval.isdigit():
                        return int(sval)
                except Exception:
                    pass
            return None

        out: List[dict] = []
        output_assets: List[Asset] = []

        current_section: dict | None = None
        buffer_parts: List[str] = []

        def update_section_text() -> None:
            if current_section is None:
                return
            current_section['text'] = "\n\n".join([p for p in buffer_parts if p and str(p).strip()])

        def start_section(title_text: str, meta: dict | None) -> None:
            nonlocal current_section, buffer_parts
            # If switching sections, finalize the previous one
            update_section_text()
            # Begin new section and append immediately to preserve order
            current_section = {
                'type': ElementType.TITLE.value,
                'text': '',
                'metadata': {
                    'section_title': title_text,
                    'heading_level': 1,
                    'title_metadata': meta or {}
                }
            }
            out.append(current_section)
            buffer_parts = []
            if title_text:
                buffer_parts.append(title_text)
            update_section_text()

        for el in elements:
            el_type = el.get('type')
            el_text = el.get('text', '') or ''
            el_meta = (el.get('metadata') or {})

            # Extract assets for images and emit a standalone Image node
            if el_type == ElementType.IMAGE.value:
                asset = Asset(
                    uuid=el.get('element_id'),
                    data_mimetype=el_meta.pop('image_mime_type', None) or '',
                    data_base64=el_meta.pop('image_base64', None) or '',
                    description=cls.parse_raw_description(el_text)
                )
                output_assets.append(asset)
                # Ensure a section exists and include caption text
                if el_text and el_text.strip():
                    if current_section is None:
                        start_section(title_text='Preface', meta={})
                    buffer_parts.append(el_text)
                    update_section_text()
                # Emit Image node with asset linkage
                out.append({
                    'type': ElementType.IMAGE.value,
                    'text': el_text,
                    'metadata': {**el_meta, 'asset_uuid': el.get('element_id')},
                    'element_id': el.get('element_id')
                })
                continue

            # Title handling
            if el_type == ElementType.TITLE.value:
                lvl = heading_level(el_meta)
                if lvl is None or lvl == 1:
                    # New H1 section
                    if current_section is None:
                        start_section(title_text=el_text, meta=el_meta)
                    else:
                        start_section(title_text=el_text, meta=el_meta)
                else:
                    # Lower-level title stays in the current section
                    if current_section is None:
                        start_section(title_text='Preface', meta={})
                    if el_text and el_text.strip():
                        buffer_parts.append(el_text)
                        update_section_text()
                continue

            # Table handling: emit as standalone node while keeping current section
            if el_type == ElementType.TABLE.value:
                # Ensure a section exists
                if current_section is None:
                    start_section(title_text='Preface', meta={})
                # Flush current text into the section
                update_section_text()
                # Append the table element as-is (copy to avoid side-effects)
                out.append({
                    'type': ElementType.TABLE.value,
                    'text': el_text,
                    'metadata': el_meta,
                    'element_id': el.get('element_id')
                })
                # Continue accumulating more text in the same section afterwards
                continue

            # Any other content joins the current section
            if current_section is None:
                start_section(title_text='Preface', meta={})
            if el_text and str(el_text).strip():
                buffer_parts.append(str(el_text))
                update_section_text()

        # Finalize last section text
        update_section_text()

        return out, output_assets