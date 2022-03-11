import requests
import re
import time

from reference_extractors.german_wiki_article_extractor import GermanWikipediaArticleReferenceExtractor
from reference_extractors.reference_extractor import ReferenceExtractor

class WikiArticle:
    '''
        Encapsulation of the Article, with default implementation. Alternatives could store the html permanently
        instead of only storing the reference.
    '''
    # Vision for Extension: Implement static factory method that selects the appropriate extractor for an Article based on url.
    # Eg: de.wikipedia.org/* -> German extractor
    # en.wikipedia.org/* -> English extractor
    def __init__(self, url, reference_extractor: ReferenceExtractor = GermanWikipediaArticleReferenceExtractor(), session = None) -> None:
        """Initializes the WikiArticle

        Args:
            url (str): Url to the represented wikipedia article
            session (requests.Session, optional): Optional: The Request Session within which the articles contents are retrieved. Accelarates mass creation of WikiArticle objects. Defaults to None.
        """
        self.session = session
        self.__reference_extractor = reference_extractor
        self._html_cache = None
        self.url = url
        self._html_cache = self.html      
        self.title = re.search(r'<h1 id="firstHeading" .*?>(.*?)</h1>', self.html).group(1)
    @property
    def html(self):
        """Html of the article page

        Returns:
            str: Html of the wikipedia page
        """                                                                                                                                         
        if self._html_cache:
            return self._html_cache
        elif self.session != None:
            response = self.session.get(self.url)
        else:
            response = requests.get(self.url)
        return response.content.decode("UTF_8")
    @property
    def references(self):
        """Contains all references, attemptedly filtered to only include references to articles.

        Returns:
            list[str]: reference urls to wikipedia articles referenced within this one.
        """
        html = self.html
        # Apply the Reference extractor to the html.
        references = self.__reference_extractor(html)
        self._html_cache = None
        return references
    
    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, WikiArticle) and self.url == __o.url
    def __ne__(self, __o: object) -> bool:
        return not self == __o
    
if __name__ == "__main__":
    """Test is run if the module is executed.
    """
    session = requests.Session()
    article =WikiArticle("https://de.wikipedia.org/wiki/Harry_Potter_%28Filmreihe%29", session=session)
    start = time.time()
    references = article.references
    for reference in article.references:
        WikiArticle(reference, session)
    ex_time = time.time() - start
    print(f"took {ex_time} to get {len(references)} refs and create articles.")
    