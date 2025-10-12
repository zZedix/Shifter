"""Execute the Shifter CLI when running ``python -m shifter``."""

from .cli import cli


def main() -> None:
    """Entrypoint used by ``python -m shifter``."""
    cli.main(prog_name="shifter")


if __name__ == "__main__":
    main()
