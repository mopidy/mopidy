import configparser
import io

from mopidy.internal import validation

import xml.etree.ElementTree as elementtree  # noqa: N813


def parse(data):
    handlers = {
        detect_extm3u_header: parse_extm3u,
        detect_pls_header: parse_pls,
        detect_asx_header: parse_asx,
        detect_xspf_header: parse_xspf,
    }
    for detector, parser in handlers.items():
        if detector(data):
            return list(parser(data))
    return list(parse_urilist(data))  # Fallback


def detect_extm3u_header(data):
    return data[0:7].upper() == b"#EXTM3U"


def detect_pls_header(data):
    return data[0:10].lower() == b"[playlist]"


def detect_xspf_header(data):
    data = data[0:150]
    if b"xspf" not in data.lower():
        return False

    try:
        data = io.BytesIO(data)
        for _event, element in elementtree.iterparse(data, events=(b"start",)):
            return element.tag.lower() == "{http://xspf.org/ns/0/}playlist"
    except elementtree.ParseError:
        pass
    return False


def detect_asx_header(data):
    data = data[0:50]
    if b"asx" not in data.lower():
        return False

    try:
        data = io.BytesIO(data)
        for _event, element in elementtree.iterparse(data, events=(b"start",)):
            return element.tag.lower() == "asx"
    except elementtree.ParseError:
        pass
    return False


def parse_extm3u(data):
    # TODO: convert non URIs to file URIs.
    found_header = False
    for line in data.splitlines():
        if found_header or line.startswith(b"#EXTM3U"):
            found_header = True
        else:
            continue

        if not line.strip() or line.startswith(b"#"):
            continue

        try:
            line = line.decode()
        except UnicodeDecodeError:
            continue

        yield line.strip()


def parse_pls(data):
    # TODO: convert non URIs to file URIs.
    try:
        cp = configparser.RawConfigParser()
        cp.read_string(data.decode())
    except configparser.Error:
        return

    for section in cp.sections():
        if section.lower() != "playlist":
            continue
        for i in range(cp.getint(section, "numberofentries")):
            yield cp.get(section, f"file{i + 1}").strip("\"'")


def parse_xspf(data):
    try:
        # Last element will be root.
        for _event, element in elementtree.iterparse(io.BytesIO(data)):
            element.tag = element.tag.lower()  # normalize
    except elementtree.ParseError:
        return

    ns = "http://xspf.org/ns/0/"
    path = f"{{{ns}}}tracklist/{{{ns}}}track"
    for track in element.iterfind(path):
        yield track.findtext(f"{{{ns}}}location")


def parse_asx(data):
    try:
        # Last element will be root.
        for _event, element in elementtree.iterparse(io.BytesIO(data)):
            element.tag = element.tag.lower()  # normalize
    except elementtree.ParseError:
        return

    for ref in element.findall("entry/ref[@href]"):
        yield ref.get("href", "").strip()

    for entry in element.findall("entry[@href]"):
        yield entry.get("href", "").strip()


def parse_urilist(data):
    for line in data.splitlines():
        if not line.strip() or line.startswith(b"#"):
            continue

        try:
            line = line.decode()
        except UnicodeDecodeError:
            continue

        try:
            validation.check_uri(line)
        except ValueError:
            continue

        yield line.strip()
