"""Stage and audit Task 03H inputs without reading source PDFs or model files."""

from er_commons.document_publication.task03h_preparation import prepare_task03h
from er_commons.settings import load_settings


def main() -> None:
    """Prepare the configured external data root and print the readiness report path."""
    print(prepare_task03h(load_settings().data_root))


if __name__ == "__main__":
    main()
