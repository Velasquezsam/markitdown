import io
import sys
from pathlib import Path
from typing import Any, BinaryIO, Sequence

from markitdown._exceptions import MarkItDownException
from markitdown._markitdown import MarkItDown
from markitdown._stream_info import StreamInfo


def output_filename(filename: str) -> str:
    """Return the Markdown filename corresponding to an uploaded filename."""
    return f"{Path(filename).stem}.md"


def format_file_size(size: int) -> str:
    """Return a compact, human-readable file size."""
    if size < 1024:
        return f"{size} B"
    if size < 1024**2:
        return f"{size / 1024:.1f} KB"
    return f"{size / 1024**2:.1f} MB"


def conversion_counts(
    results: Sequence[tuple[str, str]], errors: Sequence[tuple[str, str]]
) -> tuple[int, int, int]:
    """Return selected, successful, and failed conversion counts."""
    return len(results) + len(errors), len(results), len(errors)


def convert_uploaded_file(uploaded_file: Any, converter: MarkItDown) -> str:
    """Convert a Streamlit uploaded file using MarkItDown's stream API."""
    filename = str(uploaded_file.name)
    extension = Path(filename).suffix or None
    stream: BinaryIO = io.BytesIO(uploaded_file.getvalue())
    result = converter.convert(
        stream,
        stream_info=StreamInfo(
            filename=filename,
            extension=extension,
            mimetype=getattr(uploaded_file, "type", None),
        ),
    )
    return result.markdown


def render_app() -> None:
    import streamlit as st

    st.set_page_config(
        page_title="MarkItDown | Conversor",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
        .hero {
            padding: 1.5rem 1.75rem;
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 1rem;
            background: linear-gradient(135deg, rgba(0, 128, 255, 0.14), rgba(128, 0, 255, 0.08));
            margin-bottom: 1.25rem;
        }
        .hero h1 { margin: 0 0 .35rem; letter-spacing: -.03em; }
        .hero p { margin: 0; opacity: .8; }
        .step-card {
            min-height: 5.2rem;
            padding: .8rem 1rem;
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: .75rem;
        }
        .step-card strong { display: block; margin-bottom: .25rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="hero">
            <h1>📝 MarkItDown</h1>
            <p>Convierte tus archivos a Markdown limpio, estructurado y listo para usar.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    steps = st.columns(3)
    for column, number, title, description in zip(
        steps,
        ("01", "02", "03"),
        ("Carga", "Convierte", "Descarga"),
        (
            "Selecciona uno o varios archivos.",
            "Procesamos cada archivo por separado.",
            "Revisa y descarga tu Markdown.",
        ),
    ):
        with column:
            st.markdown(
                f'<div class="step-card"><strong>{number} · {title}</strong>{description}</div>',
                unsafe_allow_html=True,
            )

    uploaded_files = st.file_uploader(
        "Archivos de entrada",
        accept_multiple_files=True,
        help="Puedes seleccionar varios archivos para convertirlos en una sola sesión.",
        label_visibility="visible",
    )
    if uploaded_files:
        st.caption(
            f"{len(uploaded_files)} archivo(s) seleccionado(s). "
            "Puedes añadir más archivos antes de convertir."
        )

    action_columns = st.columns([1, 1, 4])
    with action_columns[0]:
        convert_clicked = st.button(
            "Convertir archivos",
            type="primary",
            disabled=not uploaded_files,
            use_container_width=True,
        )
    with action_columns[1]:
        if st.button("Nueva conversión", use_container_width=True):
            st.session_state.pop("conversion_results", None)
            st.session_state.pop("conversion_errors", None)
            st.rerun()

    if convert_clicked:
        converter = MarkItDown()
        results: list[tuple[str, str]] = []
        errors: list[tuple[str, str]] = []
        progress = st.progress(0, text="Preparando conversión...")

        for index, uploaded_file in enumerate(uploaded_files):
            progress.progress(
                index / len(uploaded_files),
                text=f"Convirtiendo {uploaded_file.name}...",
            )
            try:
                markdown = convert_uploaded_file(uploaded_file, converter)
                results.append((uploaded_file.name, markdown))
            except MarkItDownException as exc:
                errors.append((uploaded_file.name, f"{type(exc).__name__}: {exc}"))

        progress.progress(1.0, text="Conversión completada")
        st.session_state["conversion_results"] = results
        st.session_state["conversion_errors"] = errors

    results = st.session_state.get("conversion_results", [])
    errors = st.session_state.get("conversion_errors", [])
    selected_count, success_count, error_count = conversion_counts(results, errors)

    if selected_count:
        st.divider()
        metric_columns = st.columns(3)
        metric_columns[0].metric("Archivos procesados", selected_count)
        metric_columns[1].metric("Convertidos", success_count)
        metric_columns[2].metric("Con errores", error_count)

    for filename, error in errors:
        with st.expander(f"⚠️ No se pudo convertir: {filename}", expanded=True):
            st.error(error)
            st.caption("Revisa el formato o instala la dependencia opcional requerida.")

    for index, (filename, markdown) in enumerate(results):
        with st.container(border=True):
            header_columns = st.columns([4, 1])
            with header_columns[0]:
                st.subheader(filename)
                st.caption(
                    f"Resultado listo · {format_file_size(len(markdown.encode('utf-8')))}"
                )
            with header_columns[1]:
                st.download_button(
                    "Descargar .md",
                    data=markdown,
                    file_name=output_filename(filename),
                    mime="text/markdown",
                    key=f"download-{index}-{filename}",
                    use_container_width=True,
                )
            preview_tab, markdown_tab = st.tabs(["Vista previa", "Markdown"])
            with preview_tab:
                st.markdown(markdown)
            with markdown_tab:
                st.code(markdown, language="markdown")


def main() -> None:
    """Launch the Streamlit application through the package script."""
    from streamlit.web.cli import main as streamlit_main

    sys.argv = ["streamlit", "run", str(Path(__file__))] + sys.argv[1:]
    streamlit_main()


if __name__ == "__main__":
    render_app()
