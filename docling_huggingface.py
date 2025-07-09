from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
from docling.datamodel.pipeline_options import (
    VlmPipelineOptions,
)
from docling.datamodel.pipeline_options_vlm_model import InlineVlmOptions, InferenceFramework, TransformersModelType, ResponseFormat, AcceleratorDevice

pipeline_options = VlmPipelineOptions(
    vlm_options=InlineVlmOptions(
        repo_id="google/gemma-3n-e2b-it",
        prompt="Chuyển trang này sang định dạng Markdown. Không được bỏ sót bất kỳ nội dung nào và chỉ xuất ra Markdown thuần túy!",
        response_format=ResponseFormat.MARKDOWN,
        inference_framework=InferenceFramework.TRANSFORMERS,
        transformers_model_type=TransformersModelType.AUTOMODEL,
        supported_devices=[
            AcceleratorDevice.CUDA,
            AcceleratorDevice.CPU
        ],
        scale=2.0,
        temperature=0.0,
        torch_dtype="bfloat16",
    )
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_cls=VlmPipeline,
            pipeline_options=pipeline_options,
        ),
    }
)

doc = converter.convert(source="quy_dinh_hoc_vu_va_dao_tao.pdf").document
print(doc.export_to_markdown())