import ipfshttpclient

def uploadImageIPFS(image):
    client = ipfshttpclient.connect()
    fileBytes = image.file.read()
    res = client.add(fileBytes)

    cid = res['Hash']
    return cid