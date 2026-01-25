import shutil
import pymupdf
from pathlib import Path
from manga_processor.models import Manga, MangaPagePath


class MangaNormalizer:
    def normalize(self, input_dir: Path, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)

        files = [f for f in input_dir.iterdir() if f.is_file()]
        files.sort(key=lambda f: (int(f.stem) if f.stem.isdigit() else f.stem))

        for i, file in enumerate(files):
            if not file.is_file():
                raise IsADirectoryError(f"{file} is a directory")

            ext = file.suffix.lower()

            match ext:
                case ".pdf":
                    self._process_pdf(file, output_dir)
                case ".png" | ".jpg" | ".jpeg":
                    new = output_dir / f"{i}.png"
                    shutil.copyfile(file, new)
                case _:
                    raise ValueError(f"Unsupported file type: {ext}")

    def _process_pdf(self, pdf_path: Path, output_dir: Path) -> None:
        doc = pymupdf.open(pdf_path)
        for page in doc:
            pix = page.get_pixmap()
            pix.save(output_dir / f"{page.number}.png")


class MangaLoader:
    def __init__(self, normalizer: MangaNormalizer):
        self.normalizer = normalizer

    def load_directory(self, path: Path) -> Manga:
        normalized_dir = path.parent / f"{path.name}_normalized"
        self.normalizer.normalize(path, normalized_dir)

        files = [f for f in normalized_dir.iterdir() if f.is_file()]
        files.sort(key=lambda f: (int(f.stem) if f.stem.isdigit() else f.stem))

        pages: list[MangaPagePath] = []
        for i, file in enumerate(files):
            if file.suffix.lower() == ".png":
                pages.append(MangaPagePath(index=i, path=file))

        manga = Manga(pages=pages, dir_path=normalized_dir)
        return manga
