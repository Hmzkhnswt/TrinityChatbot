import os
import json
from typing import Optional, List, Dict
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import logging
import uuid
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


class SSRScraper:
    def __init__(self, 
                 use_selenium: bool = False,
                 max_pages: int = 100,
                 timeout: int = 30,
                 max_retries: int = 3,
                 concurrent_requests: int = 5,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        self.use_selenium = use_selenium
        self.max_pages = max_pages
        self.timeout = timeout
        self.max_retries = max_retries
        self.concurrent_requests = concurrent_requests
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize sets for tracking
        self.visited_urls = set()
        self.failed_urls = set()
        
        # Setup headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        # Initialize session for connection pooling
        self.session = requests.Session()

        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=50, max_retries=self.max_retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        if use_selenium:
            self._setup_selenium()

        # Ensure artifacts directory exists
        self.artifacts_dir = "artifacts"
        os.makedirs(self.artifacts_dir, exist_ok=True)

    def _setup_selenium(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(self.timeout)

    def _get_with_selenium(self, url: str) -> Optional[str]:
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)
            return self.driver.page_source
        except TimeoutException:
            self.logger.error(f"Selenium timeout on URL: {url}")
            return None
        except Exception as e:
            self.logger.error(f"Selenium error on URL {url}: {str(e)}")
            return None

    def _get_with_requests(self, url: str) -> Optional[str]:
        try:
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error on URL {url}: {str(e)}")
            return None

    def _extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        text = soup.get_text(separator=' ')
        text = ' '.join(text.split())
        return text

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        base_domain = urlparse(base_url).netloc
        
        links = []
        for link in soup.find_all('a', href=True):
            url = urljoin(base_url, link['href'])
            if urlparse(url).netloc == base_domain:
                links.append(url)
        
        return list(set(links))
    

    def _create_langchain_documents(self, text: str, url: str, token: str) -> List[Document]:
        timestamp = datetime.now().isoformat()
        
        # Split text into chunks
        texts = self.text_splitter.split_text(text)
        
        # Create documents with metadata
        if "trakx" in url:
            token = "trakx"
        elif "bidnow" in url:
            token = "bidnow"
        else:
            token = "unknown"  # Optional: handle cases where no match is found


        documents = [
            Document(
                page_content=chunk,
                metadata={ 
                    '_id': str(uuid.uuid4()), 
                    "source": url, 
                    "timestamp": timestamp,
                    "token": token
                }
            )
            for chunk in texts
        ]
        
        return documents


    def _save_documents(self, documents: List[Document], url: str):
        filename = os.path.join(self.artifacts_dir, f"{uuid.uuid4()}.json")
        
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump([doc.dict() for doc in documents], file, ensure_ascii=False, indent=4)

        self.logger.info(f"Saved {len(documents)} documents to {filename}")


    def scrape_url(self, url: str, depth: int = 0, token: str = "") -> Dict:
        if url in self.visited_urls or url in self.failed_urls:
            return {}
        
        self.visited_urls.add(url)
        
        for attempt in range(self.max_retries):
            try:
                html = (self._get_with_selenium(url) if self.use_selenium 
                    else self._get_with_requests(url))
                
                if not html:
                    continue
                
                text_content = self._extract_text(html)
                links = self._extract_links(html, url)
                documents = self._create_langchain_documents(text_content, url, token)

                for doc in documents:
                    print(f"Extracted Document: {doc.page_content}\n")
                self._save_documents(documents, url)
                
                return {
                    'documents': documents,
                    'links': links,
                    'depth': depth
                }
                
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed for URL {url}: {str(e)}")
                time.sleep(1)
        
        self.failed_urls.add(url)
        return {}


    def scrape_site(self, start_url: str, max_depth: int = 2) -> List[Document]:
        self.logger.info(f"Starting scrape of {start_url}")
        
        all_documents = []
        to_scrape = [(start_url, 0)]  
        
        with ThreadPoolExecutor(max_workers=self.concurrent_requests) as executor:
            while to_scrape and len(self.visited_urls) < self.max_pages:
                current_batch = []
                while to_scrape and len(current_batch) < self.concurrent_requests:
                    url, depth = to_scrape.pop(0)
                    
                    if url not in self.visited_urls and url not in self.failed_urls:
                        current_batch.append((url, depth))
                
                if not current_batch:
                    continue
                
                future_to_url = {
                    executor.submit(self.scrape_url, url, depth): (url, depth)
                    for url, depth in current_batch
                }
                
                for future in future_to_url:
                    url, depth = future_to_url[future]
                    try:
                        result = future.result()
                        
                        if result and 'documents' in result and 'links' in result:
                            all_documents.extend(result['documents'])
                            
                            if depth < max_depth and len(self.visited_urls) < self.max_pages:
                                new_urls = [
                                    (link, depth + 1) for link in result['links']
                                    if link not in self.visited_urls and link not in self.failed_urls
                                ]
                                to_scrape.extend(new_urls)
                        else:
                            self.logger.warning(f"Unexpected result format from {url}: {result}")
                    
                    except Exception as e:
                        self.logger.error(f"Error processing {url}: {str(e)}")
                        self.failed_urls.add(url) 
            
            self.logger.info(f"Scraping completed. Processed {len(self.visited_urls)} URLs")
        
        return all_documents


    def cleanup(self):
        if self.use_selenium:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.error(f"Error closing Selenium driver: {str(e)}")