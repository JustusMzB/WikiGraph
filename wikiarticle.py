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
        self.__session = session
        self.__reference_extractor = reference_extractor
        self.url = url
        if not url.startswith("https://"):
            raise ValueError(f'Article creation with Schema-less url: {url} was attempted.')
        # Filling the html cache. Needs to be initialized, as html method is accessing it.
        self.__html_cache = None
        self.__html_cache = self.html      
        self.title = re.search(r'<h1 id="firstHeading" .*?>(.*?)</h1>', self.html).group(1)
    @property
    def html(self):
        """Html of the article page

        Returns:
            str: Html of the wikipedia page
        """                                                                                                                                         
        if self.__html_cache:
            return self.__html_cache
        elif self.__session != None:
            response = self.__session.get(self.url)
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
        # In the graph creation process, this is the last time that html is needed. Therefore, the cache is dropped.
        self.__html_cache = None
        return references
    
    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, WikiArticle) and self.url == __o.url
    def __ne__(self, __o: object) -> bool:
        return not self == __o
    def __str__(self) -> str:
        return f'<WikiArticle: title = {self.title}; url= {self.url}> '
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
    