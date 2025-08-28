import ipfshttpclient

def uploadImageIPFS(image):
    client = ipfshttpclient.connect()
    fileBytes = image.file.read()
    res = client.add_bytes(fileBytes)

    return res

def fileRetrieve(cid):
    
    pass