import yaml

def get_cont_names(doc, cont_name_set):
    try:
        if isinstance(doc, dict):
            for k,v in doc.items():
                if k == 'containers':
                    for elem in v:
                        cont_name = elem['name']
                        cont_name_set.add(cont_name)
                        #print("Container name:%s" % cont_name)
                else:
                    get_cont_names(v, cont_name_set)
    except Exception as e:
        print(str(e))
#    return cont_name_set

def main():
    stream = open("bookinfo-test.yaml", "r")
    docs = yaml.load_all(stream)
    cont_name_set = set()
    for doc in docs:
        get_cont_names(doc, cont_name_set)
    print("Container names: %s" % cont_name_set)

if __name__ == '__main__':
    main()




