import glob
import io
import json
import os
import re
import ssl
from elastic_enterprise_search import AppSearch
from oauth2client.file import Storage
from oauth2client import client
from oauth2client import tools
import httplib2
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from apiclient import discovery
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
from io import StringIO
from pdfminer.pdfpage import PDFPage
from pdf2image import convert_from_path
from pprint import pprint


class Jurisprudence:
    def __init__(self,code,date,principle,title,content,sujet,keywords,reference,year):
        self.id=code
        self.date=date
        self.principle=principle
        self.code=code
        self.year=year
        self.room_ar="مجلس الدولة"
        self.title=title
        self.room="Conseil d'État"
        self.decision=content
        self.sujet=sujet
        self.keywords=keywords
        self.reference=reference

def convertpdf2image(path_to_pdf):
    images = convert_from_path(path_to_pdf)
    for i in range(0, len(images)):
        images[i].save("page" + str(i + 1) + ".jpg", "JPEG")

def get_credentials():
    # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/drive-python-quickstart.json
    SCOPES = 'https://www.googleapis.com/auth/drive'
    CLIENT_SECRET_FILE = 'client_secret_395744274280-ot1ar85i1306dvbo7ql1a7rqblc3j1bn.apps.googleusercontent.com.json'
    APPLICATION_NAME = 'Drive API Python Quickstart'

    credential_path = os.path.join("./", 'drive-python-quickstart.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def ocr(file):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    imgfile = file + '.jpg'  # Image with texts (png, jpg, bmp, gif, pdf)
    txtfile = file + '.txt'  # Text file outputted by OCR

    mime = 'application/vnd.google-apps.document'
    res = service.files().create(
        body={
            'name': imgfile,
            'mimeType': mime
        },
        media_body=MediaFileUpload(imgfile, mimetype=mime, resumable=True)
    ).execute()
    print(f"txtfile: {txtfile}")
    downloader = MediaIoBaseDownload(
        io.FileIO(txtfile, 'wb'),
        service.files().export_media(fileId=res['id'], mimeType="text/plain")
    )
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    service.files().delete(fileId=res['id']).execute()
    print("Done.")

def injectdataVSC(json):
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context

    app_search = AppSearch(
        "https://vps.juriste-dz.com/",  # Endpoint
        http_auth="private-tr1mjxvtsg5e66dntc2x6pb3",
        # Private key, grants read/write access only to the engine "journal-officiel-veille"
        ca_certs=False,
        verify_certs=False,
    )
    engine_name = "jurisprudences-veille"
    response = app_search.index_documents(
        engine_name=engine_name,
        body=json, request_timeout=30
    )

def ocrpages():
    for i in range(1, 3):
        ocr("page" + str(i))
        os.remove("page" + str(i) + ".jpg")



def grouptext():
    filesommaire = open("text.txt", "w", encoding="UTF-8")
    for i in range(1, 3):
        file = open("page" + str(i) + ".txt", "r", encoding='UTF-8')
        filesommaire.write(file.read())
        file.close()
        os.remove("page" + str(i) + ".txt")
    filesommaire.close()


def traitement(file):
    convertpdf2image(file)
    ocrpages()
    grouptext()
    file = open("text.txt","r",encoding="UTF-8")
    lines=file.readlines()
    print(lines)
    for line in lines:
        pos=line.find("رقم")
        if pos!=-1:
            print(line)
            print(line[pos+4:pos+10])
            code=line[pos+4:pos+10]
            break

    for line in lines:
        pos=line.find("/")
        if pos!=-1:
            print(line)
            print(line[pos-2:pos+10])
            date=line
            break

    for line in lines:
        pos=line.find("-")
        if pos!=-1:
            print(line)
            print(line)
            keywords=line
            break
    file.seek(0)
    text=file.read()
    allmatches = re.finditer(pattern="مبدأ", string=text)
    for m in allmatches:
        start=m.start()
        break
    allmatches = re.finditer(pattern="مجلس الدولة", string=text[start:])
    for m in allmatches:
        end=m.start()
        break
    principe=text[start:end]
    print("principe")
    print(start)
    print(end)
    allmatches = re.finditer(pattern="مجلس الدولة", string=text)
    for m in allmatches:
        start=m.start()
        break

    content=text[start:]
    date=date.replace("/","-")
    year=date[0:4]
    juris=Jurisprudence(code,date,principe,"",content,"",keywords," ",year)
    pprint(vars(juris))
    json_str = json.dumps([juris.__dict__])
    file=open("arret demo.json","w",encoding="UTF-8")
    file.write(json_str)
    file.close()
    print(json_str)
    injectdataVSC(json_str)


read_files = glob.glob("./*.pdf")

for file in read_files:
    try:
        traitement(file)
    except:
        print("error")

