import pymupdf
import os

class Document:
    def __init__(self, path):
        self.path = path

    def save_to_pdf(self, output_path=None):
        if not output_path:
            output_path = self.path.join("/pdf")
            
        filedir = self.path

        try:
            filelist = os.listdir(filedir)

            doc = pymupdf.open()

            for i, f in enumerate(filelist):
                file_path = os.path.join(filedir, f)
                _n, ext = os.path.splitext(file_path)
                match ext:
                    case ".pdf":
                        pdf_page = pymupdf.open(file_path)
                        doc.insert_pdf(pdf_page)
                        pdf_page.close()
                    case ".jpg" | ".jpeg" | ".png":
                        self._convert_img_to_page(f, filedir, doc)
                    case _:
                        raise pymupdf.FileDataError("Invalid data type")
            
                        
            doc.save(output_path)
        except Exception as e:
            print("Failed saving to pdf:", e)
            raise

    def _convert_img_to_page(self, file, imgdir, doc):

        img_path = os.path.join(imgdir, file)
        try:
            img = pymupdf.open(img_path)
            rect = img[0].rect
            pdfbytes = img.convert_to_pdf()
            img.close()
            imgPDF = pymupdf.open("pdf", pdfbytes)
            page = doc.new_page(width=rect.width, height=rect.height)
            page.show_pdf_page(rect, imgPDF, 0)
        except Exception as e:
            print(f"Failed while processing {img_path} with:", e)
            raise

