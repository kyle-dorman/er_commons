"""Stage and audit Task 03G.2 inputs without reading source PDFs."""

from er_commons.document_publication.task03g2_preparation import prepare_task03g2
from er_commons.settings import load_settings


def main() -> None:
    """Prepare the configured external data root and print the report path."""
    print(prepare_task03g2(load_settings().data_root))


if __name__ == "__main__":
    main()
