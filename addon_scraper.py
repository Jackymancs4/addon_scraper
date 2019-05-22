import errno
import shutil
import zipfile
from os import listdir, makedirs, remove
from os.path import exists, isfile, join

from utils import *

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from git import Repo

def create_addon_repo (addon_name, debug = False):

    amo_url = "https://addons.mozilla.org/it/firefox/addon/"

    dprint("Start", debug)
    dprint("", debug)

    print("Retrieving addon data")
    version_array = get_versions(addon_name, amo_url, debug)
    dprint(version_array, debug)
    print("Got all data!")
    print()

    print("Start download all addons archives")
    download_xpi(addon_name, False, version_array)
    print("Got all files!")
    print()

    print("Start archive unzipping and repo creation")
    unzip_files(addon_name, False, version_array)
    print("Repo created!")
    print()

    # print("Cleaning up")
    # clean_temp(addon_name)
    # print("Finished!")


def get_versions(addon_name, amo_url, debug):

    version_page_base_url = amo_url + addon_name + "/versions/?page="
    version_array = get_versions_by_page(version_page_base_url, 1)
    version_array.reverse()
    return version_array

def get_versions_by_page(version_page_base_url, page=1):

    version_page_url = version_page_base_url + str(page)

    version_page = requests.get(version_page_url)
    version_page_content = version_page.content

    html_parser = BeautifulSoup(version_page_content, features="html.parser")
    versions = html_parser.find_all("div", class_="version item")

    version_array = []
    for version in versions:
        version_element = {}
        version_element["id"] = version["id"][8:]
        version_element["release"] = parse(
            version.find("div", class_="info").h3.span.time["datetime"]
        )
        version_element["desc"] = version.find("div", class_="desc prose").get_text().strip()
        version_element["address"] = version.find("div", class_="action").div.div.p.a["href"][
            : -len("?src=version-history")
        ]

        version_array.append(version_element)

    nextButton = html_parser.find_all("a", class_="button next")

    if nextButton != [] and nextButton[0]["href"] != "#":
        version_array.append(get_versions_by_page(version_page_base_url, page + 1))

    return version_array


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


def download_xpi(name, clean, versions):

    temp_path = get_temp_path(name)

    if clean:
        clean_temp(name)

    create_folder(temp_path)

    for version in versions:

        zname = join(temp_path, version["id"] + ".zip")

        if not isfile(zname):
            resp = requests.get(version["address"])

            zfile = open(zname, "wb")
            zfile.write(resp.content)
            zfile.close()

    return True


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


def unzip_files(name, clean, versions):

    zfolder = get_git_path(name)
    temp_path = get_temp_path(name)

    if clean:
        remove_folder(zfolder)

    repo = Repo.init(zfolder)
    # repo.git.branch("master")

    for version in versions:

        if version["id"] not in repo.tags:

            clean_up_repo(name)

            zname = join(temp_path, version["id"] + ".zip")

            zip_ref = zipfile.ZipFile(zname, "r")
            zip_ref.extractall(zfolder)
            zip_ref.close()

            shutil.rmtree(zfolder + "/META-INF", ignore_errors=True)

            repo.git.add("*")
            repo.git.commit(m="Version " + version["id"] + "\n" + version["desc"])
            repo.create_tag(version["id"])


# extension_name = "night_owl"
# create_addon_repo(extension_name, True)
