import shutil
import pymupdf
from pathlib import Path
from manga_processor.models import Manga, MangaPagePath


class MangaNormalizer:
    def normalize(self, input_dir: Path, output_dir: Path) -> None:
        print(f"Normalizing directory: {input_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Force absolute path and use glob to find files
        input_path = input_dir.resolve()
        files = (
            list(input_path.glob("*.png"))
            + list(input_path.glob("*.jpg"))
            + list(input_path.glob("*.pdf"))
        )

        print(f"Normalizer found {len(files)} files to process")

        # Sort them properly
        files.sort(key=lambda f: (int(f.stem) if f.stem.isdigit() else f.stem))

        for i, file in enumerate(files):
            print(f"Processing: {file.name} -> {i}.png")
            ext = file.suffix.lower()

            match ext:
                case ".pdf":
                    self._process_pdf(file, output_dir)
                case ".png" | ".jpg" | ".jpeg":
                    new = output_dir / f"{i}.png"
                    shutil.copyfile(str(file), str(new))  # Use str() to be safe
                case _:
                    print(f"Skipping unsupported file: {file.name}")

    def _process_pdf(self, pdf_path: Path, output_dir: Path) -> None:
        doc = pymupdf.open(pdf_path)
        for page in doc:
            pix = page.get_pixmap()
            pix.save(output_dir / f"{page.number}.png")


class MangaLoader:
    def __init__(self, normalizer: MangaNormalizer):
        self.normalizer = normalizer

    def load_directory(self, path: Path) -> Manga:
        print(f"loading directory {path}")
        stuff_in_dir = list(path.iterdir())
        print(f"{stuff_in_dir}")
        normalized_dir = path.parent / f"{path.name}_normalized"
        self.normalizer.normalize(path, normalized_dir)
        print(f"files after norm: {list(normalized_dir.iterdir())}")
        files = [f for f in normalized_dir.iterdir() if f.is_file()]
        files.sort(key=lambda f: (int(f.stem) if f.stem.isdigit() else f.stem))

        pages: list[MangaPagePath] = []
        for i, file in enumerate(files):
            if file.suffix.lower() == ".png":
                print(f"creating a manga page path of {file}")
                pages.append(MangaPagePath(index=i, path=file))

        manga = Manga(pages=pages, dir_path=normalized_dir)
        return manga
