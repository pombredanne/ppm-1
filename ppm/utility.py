import os
import tarfile
import random
import urlparse
import shutil
import urllib2
import json
import requests

def load_json_file(depsFilePath):
    with open(depsFilePath) as fileContent:
        try:
            jsonData = json.load(fileContent)
        except ValueError:
            jsonData = {}
        except Exception:
            raise Exception("Error decoding JSON file  {f}".format(f=depsFilePath))
    return jsonData

def save_json_to_file(jsonData, depsFilePath):
    with open(depsFilePath, 'w+') as fileContent:
        try:
            jsonData = json.dump(jsonData, fileContent)
        except Exception:
            raise Exception("Error Saving JSON data to file  {f}".format(f=depsFilePath))

def generate_number(length):
    assert(length)
    return ''.join(random.choice('123456789') for x in range(length))

def url2name(url):
    return os.path.basename(urllib2.unquote(urlparse.urlsplit(url)[2]))

def post_json_data(jsonData,server):
    assert(jsonData)
    headers = {'content-type': 'application/json'}
    requests.post(server, data=json.dumps(jsonData), headers=headers)

def download_file(url, installDirectory):
    assert (url and installDirectory)
    assert (os.path.exists(installDirectory))
    localName = url2name(url)
    r = urllib2.urlopen(urllib2.Request(url))
    if 'Content-Disposition' in r.info():
        # If the response has Content-Disposition, we take file name from it
        localName = r.info()['Content-Disposition'].split('filename=')[1]
        if localName[0] == '"' or localName[0] == "'":
            localName = localName[1:-1]
    elif r.url != url:
        # if we were redirected, the real file name we take from the final URL
        localName = url2name(r.url)
    saveFilePath = joinPaths(installDirectory, localName)
    with open(saveFilePath, 'wb') as fp:
        shutil.copyfileobj(r, fp)
    r.close()
    return saveFilePath

def secure_against_path_traversal(path):
    if path is None:
        return True
    else:
        if path.startswith("/") or path.startswith(".."):
            return False
        else:
            return True

# extracting files
def extract_file(filePath, extractPath):
    assert ((os.path.exists(filePath)) and (os.path.exists(extractPath)))
    if filePath.endswith(".tar.gz"):
        extract_tar(filePath, extractPath)
        return True
    elif filePath.endswith("zip"):
        extract_zip(filePath, extractPath)
        return True
    else:
        return False

def extract_tar(filePath, extractPath):
    tar = tarfile.open(filePath)
    tar.extractall(extractPath)
    tar.close()

def extract_zip(filePath, extractPath):
    import zipfile
    with zipfile.ZipFile(filePath, "r") as z:
        z.extractall(extractPath)

def new_directory(dirPath):
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
        return True
    return False

#DIRTY: quick way to clear directory contents (without removing directory itself)
def clear_directory_contents(dirPath):
    assert os.path.isdir(dirPath)
    shutil.rmtree(dirPath)
    os.makedirs(dirPath)

def query_yes_no(question):
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    prompt = " [y/n] "
    while True:
        print(question + prompt)
        choice = raw_input().lower()
        if choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")

def move_directory_contents(src, dest):
    assert os.path.isdir(src) and os.path.isdir(dest)
    for filename in os.listdir(src):
        shutil.move(joinPaths(src, filename), joinPaths(dest, filename))

# facility on top of os..path.join to normalize paths and ignore empty strings
def joinPaths(*paths):
    return os.path.join(*[os.path.normpath(os.path.normcase(p)) for p in paths if p])

#DIRTY: quick way to print nested messages
def log(message, indentPadding=0):
    if not hasattr(log, 'indent'):
        log.indent = 0
        log.indentPattern = "  "
    print (log.indentPattern * log.indent) + message
    log.indent = log.indent + indentPadding

def ensure_directory(d):
    if not os.path.exists(d):
        os.makedirs(d)

def ensure_file_directory(f):
    d = os.path.dirname(f)
    ensure_directory(d)

def remove_file_or_dir(path):
    if not os.path.exists(path):
        return
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)
