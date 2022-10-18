from markdown_it import MarkdownIt

from translate.storage import base

_markdownit = MarkdownIt("gfm-like")


class MDUnit(base.TranslationUnit):
    """This class represents a block of text from a Markdown file"""

    def __str__(self):
        return "".join([self.pretext, self.source, self.posttext])

    @property
    def target(self):
        """gets the unquoted target string"""
        return self.source

    @target.setter
    def target(self, target):
        """Sets the definition to the quoted value of target"""
        self._rich_target = None
        self.source = target

    def addlocation(self, location):
        self.location.append(location)

    def getlocations(self):
        return self.location


class MDFile(base.TranslationStore):
    """This class represents a Markdown file, made up of MDUnits"""

    UnitClass = MDUnit

    def __init__(self, inputfile=None, flavour=None, no_segmentation=False, **kwargs):
        super().__init__(**kwargs)
        self.filename = getattr(inputfile, "name", "")
        self.flavour = flavours.get(flavour, [])
        self.no_segmentation = no_segmentation
        if inputfile is not None:
            txtsrc = inputfile.readlines()
            self.parse(txtsrc)

    def parse(self, lines):

        block = []
        current_line = 0
        pretext = ""
        posttext = ""
        if not isinstance(lines, list):
            lines = lines.split(b"\n")
        for linenum, line in enumerate(lines):
            current_line = linenum + 1
            line = line.decode(self.encoding).rstrip("\r\n")
            for _rule, prere, postre in self.flavour:
                match = prere.match(line)
                if match:
                    pretext, source = match.groups()
                    postmatch = postre.search(source)
                    if postmatch:
                        posttext = postmatch.group()
                        source = source[: postmatch.start()]
                    block.append(source)
                    isbreak = True
                    break
            else:
                isbreak = not line.strip()
            if isbreak and block:
                unit = self.addsourceunit("\n".join(block))
                unit.addlocation("%s:%d" % (self.filename, current_line))
                unit.pretext = pretext
                unit.posttext = posttext
                pretext = ""
                posttext = ""
                block = []
            elif not isbreak:
                block.append(line)
        if block:
            unit = self.addsourceunit("\n".join(block))
            unit.addlocation("%s:%d" % (self.filename, current_line))

    def serialize(self, out):
        for idx, unit in enumerate(self.units):
            if idx > 0:
                out.write(b"\n\n")
            out.write(str(unit).encode(self.encoding))