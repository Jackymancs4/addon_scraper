import errno
import shutil
import zipfile
from os import listdir, makedirs, remove
from os.path import exists, isfile, join

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from git import Repo


def get_versions(addon_name):
    data = get_versions_by_page(addon_name, 1)
    data.reverse()
    return data


def get_versions_by_page(addon_name, page=1):

    amo_url = "https://addons.mozilla.org/it/firefox/addon/"
    extentension_url = amo_url + extension_name + "/versions/?page=" + str(page)

    # print(extentension_url)

    result = requests.get(extentension_url)
    c = result.content

    soup = BeautifulSoup(c, features="html.parser")
    samples = soup.find_all("div", class_="version item")

    data = []
    for a in samples:
        version = {}
        version["id"] = a["id"][8:]
        version["release"] = parse(
            a.find("div", class_="info").h3.span.time["datetime"]
        )
        version["desc"] = a.find("div", class_="desc prose").get_text().strip()
        version["address"] = a.find("div", class_="action").div.div.p.a["href"][
            : -len("?src=version-history")
        ]

        data.append(version)

    nextButton = soup.find_all("a", class_="button next")

    if nextButton != [] and nextButton[0]["href"] != "#":
        data.append(get_versions_by_page(addon_name, page + 1))

    return data


def get_temp_path(extension_name):
    temp_folder = "tmp/" + extension_name
    return temp_folder


def get_git_path(extension_name):
    git_folder = "repos/" + extension_name
    return git_folder


def remove_folder(path):
    if exists(path):
        shutil.rmtree(path)
    return True


def clean_temp(extension_name):
    temp_path = get_temp_path(extension_name)
    remove_folder(temp_path)
    return True


def create_folder(path):
    try:
        if not exists(path):
            makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    return True


def download_xpi(name, clean, data):

    temp_path = get_temp_path(name)

    if clean:
        clean_temp(name)

    create_folder(temp_path)

    for a in data:

        zname = join(temp_path, a["id"] + ".zip")

        if not isfile(zname):
            resp = requests.get(a["address"])

            zfile = open(zname, "wb")
            zfile.write(resp.content)
            zfile.close()


def clean_up_repo(name):
    mypath = get_git_path(name)
    list_repo_content = listdir(mypath)
    for f in list_repo_content:
        if f == ".git":
            pass
        elif isfile(join(mypath, f)):
            remove(join(mypath, f))
        else:
            shutil.rmtree(join(mypath, f))


def unzip_files(name, clean, data):

    zfolder = get_git_path(name)
    temp_path = get_temp_path(name)

    if clean:
        remove_folder(zfolder)

    repo = Repo.init(zfolder)
    # repo.git.branch("master")

    for a in data:

        clean_up_repo(name)

        zname = join(temp_path, a["id"] + ".zip")

        zip_ref = zipfile.ZipFile(zname, "r")
        zip_ref.extractall(zfolder)
        zip_ref.close()

        shutil.rmtree(zfolder + "/META-INF", ignore_errors=True)

        repo.git.add("*")
        repo.git.commit(m="Version " + a["id"] + "\n" + a["desc"])
        repo.create_tag(a["id"])


extension_name = "night_owl"

print("Start")
print()

print("Retrieving addon data")
data = get_versions(extension_name)
print("Got all data!")
print()

print("Start download all addons archives")
download_xpi(extension_name, True, data)
print("Got all files!")
print()

print("Start archive unzipping and repo creation")
unzip_files(extension_name, True, data)
print("Repo created!")
print()

# print("Cleaning up")
# clean_temp(extension_name)
# print("Finished!")
