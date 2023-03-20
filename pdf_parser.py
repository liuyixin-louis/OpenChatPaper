from base_class import AbstractPDFParser
import pickle
from scipdf_utils import parse_pdf_to_dict


class GrobidSciPDFPaser(AbstractPDFParser):
    import pysbd
    seg_en = pysbd.Segmenter(language="en", clean=False)
    seg_chinese = pysbd.Segmenter(language="zh", clean=False)

    def __init__(self, pdf_link, db_name="grobid_scipdf", short_thereshold=30) -> None:
        """Initialize the PDF parser

            Args:
                pdf_link: link to the PDF file, the pdf link can be a web link or local file path
                metadata: metadata of the PDF file, like authors, title, abstract, etc.
                paragraphs: list of paragraphs of the PDF file, all paragraphs are concatenated together
                split_paragraphs: dict of section name and corresponding list of split paragraphs
        """
        super().__init__(db_name=db_name)
        self.db_name = db_name
        self.pdf_link = pdf_link
        self.pdf = None
        self.metadata = {}
        self.flattn_paragraphs = None
        self.split_paragraphs = None
        self.short_thereshold = short_thereshold
        self.parse_pdf()

    def _contact_too_short_paragraphs(self, ):
        """Contact too short paragraphs or discard them"""
        for i, section in enumerate(self.split_paragraphs):
            # section_name = section['heading']
            paragraphs = section['texts']
            new_paragraphs = []
            for paragraph in paragraphs:
                if len(paragraph) <= self.short_thereshold and len(paragraph.strip()) != 0:
                    if len(new_paragraphs) != 0:
                        new_paragraphs[-1] += paragraph
                    else:
                        new_paragraphs.append(paragraph)
                else:
                    new_paragraphs.append(paragraph)
            self.split_paragraphs[i]['texts'] = new_paragraphs

    @staticmethod
    def _find_largest_font_string(file_name, search_string):
        search_string = search_string.strip()
        max_font_size = -1
        page_number = -1
        import PyPDF2
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextContainer, LTChar
        try: 
            with open(file_name, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for index, page_layout in enumerate(extract_pages(file_name)):
                    for element in page_layout:
                        if isinstance(element, LTTextContainer):
                            for text_line in element:
                                if search_string in text_line.get_text():
                                    for character in text_line:
                                        if isinstance(character, LTChar):
                                            if character.size > max_font_size:
                                                max_font_size = character.size
                                                page_number = index
            return page_number + 1 if page_number != -1 else -1
        except Exception as e:
            return -1
        

    def _find_section_page(self, section_name) -> None:
        return GrobidSciPDFPaser._find_largest_font_string(self.pdf_link, section_name)

    def _retrive_or_parse(self, ):
        """Return pdf dict from cache if present, otherwise parse the pdf"""
        db_name = self.db_name
        if (self.pdf_link, db_name) not in self.db_cache.keys():
            self.db_cache[(self.pdf_link, db_name)
                          ] = parse_pdf_to_dict(self.pdf_link)
            with open(self.db_cache_path, "wb") as db_cache_file:
                pickle.dump(self.db_cache, db_cache_file)
        return self.db_cache[(self.pdf_link, db_name)]

    @staticmethod
    def _check_chinese(text) -> None:
        return any(u'\u4e00' <= char <= u'\u9fff' for char in text)

    def parse_pdf(self) -> None:
        """Parse the PDF file
        """
        article_dict = self._retrive_or_parse()
        self.article_dict = article_dict
        self._get_metadata()
        self.split_paragraphs = self.get_split_paragraphs()
        self._contact_too_short_paragraphs()

        self.flattn_paragraphs = self.get_paragraphs()

    def get_paragraphs(self) -> None:
        """Get the paragraphs of the PDF file
        """
        paragraphs = []
        self.content2section = {}
        for section in self.split_paragraphs:
            # paragraphs+=[section["heading"]]
            paragraphs += section["texts"]
            for para in section["texts"]:
                self.content2section[para] = section["heading"]
        return paragraphs

    def _get_metadata(self) -> None:
        for meta in ['authors', "pub_date", "abstract", "references", "doi", 'title',]:
            self.metadata[meta] = self.article_dict[meta]
        self.section_names = [section["heading"]
                              for section in self.article_dict['sections']]
        self.section_names2page = {}
        for section_name in self.section_names:
            section_page_index = self._find_section_page(section_name)
            self.section_names2page.update({section_name: section_page_index})
        self.section_names_with_page_index = [section_name + " (Page {})".format(
            self.section_names2page[section_name]) for section_name in self.section_names]

    def get_split_paragraphs(self, ) -> None:
        section_pair_list = []
        for section in self.article_dict['sections']:
            section_pair_list.append({
                "heading": section["heading"],
                "texts": section["all_paragraphs"],
            })
        return section_pair_list

    @staticmethod
    def _determine_optimal_split_of_pargraphs(section_pair_list) -> None:
        """
        split based on the some magic rules
        """
        import pysbd
        for section_pair in section_pair_list:
            if GrobidSciPDFPaser._check_chinese(section_pair["text"]):
                seg = GrobidSciPDFPaser.seg_chinese
            else:
                seg = GrobidSciPDFPaser.seg_en
            section_pair["texts"] = seg.segment(section_pair["texts"])
            section_pair["texts"] = [
                para for para in section_pair["text"] if len(para) > 2]
        return section_pair_list
