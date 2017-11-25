##
# Author: Lan
# Description: The purpose of this module is to parse in the output of the VBA-rr lua script.
# It can also generate a template structure from the parsed information, and pads it using the StructPadder module
# so that it's a programmatically usable structure template.
##
import re
import StructPadder

class MemoryAccessEntry:
    functionAddr: str
    accessAddr: int
    type: int
    offset: int
    def __init__(self, functionAddr, accessAddr, _type, offset):
        if type(functionAddr) is not str or type(accessAddr) is not int or \
                        type(_type) is not int and type(offset) is not int:
            raise(Exception("Invalid inputs to MemoryAccessEntry"))
        self.functionAddr = functionAddr
        self.accessAddr = accessAddr
        self.type = _type
        self.offset = offset


class MemoryAccessProtocol:
    _MAEntries: list  # Memory Acesss Entries
    _SMEntries: list  # Struct Member Entries
    name: str
    size: int

    def __init__(self, metaLine):
        # parse relevent meta information
        args = list(filter(None, re.split("[ \t,]", metaLine)))
        for arg in args:
            if 'name=' in arg:
                self.name = arg[5:]
            if 'size=' in arg:
                self.size = int(arg[5:], 16)
        # instantiate entries
        self._MAEntries = []
        self._SMEntries = []


    def parseline(self, line):
        args = list(filter(None, re.split("[ \t,\n]", line)))
        # if this is an entry line, the first argument will always be in the form <funcAddr>::<accessAddr>
        if len(args) == 0:
            return
        if '::' not in args[0]:
            return
        if len(args) % 2 != 0:
            return
        # parse all entries in line!
        for i in range(0, len(args), 2):
            addresses = str(args[i])  # <funcAddr>::<accessAddr>
            memAccess = str(args[i+1])  # u<type>(<offset>)
            funcAddr = addresses[:addresses.index("::")]
            accessAddr = int(addresses[addresses.index("::")+2:], 16)
            type = int(re.search(r"\d+", memAccess[:memAccess.index("(")]).group())
            offset = int(memAccess[memAccess.index("(")+1:-1], 16)
            entry = MemoryAccessEntry(funcAddr,accessAddr,type,offset)
            self._MAEntries.append(entry)

    def generate_member_entries(self):
        self._SMEntries = []
        for MAEntry in self._MAEntries:
            SMEntry = StructPadder.StructMember(_type="uint%d_t" % MAEntry.type, name= "unk_%X" % MAEntry.offset,
                                                location= MAEntry.offset, otherContent='')
            self._SMEntries.append(SMEntry)
        # All duplicated of the same type are removed
        self.remove_duplicates()
        # there could be duplicates... with different types... mark them
        self.mark_duplicates()

    def no_SMEntry_duplicate_in(self, newSMEntries, SMEntry):
        output = True
        for entry in newSMEntries:
            if entry.location == SMEntry.location and entry.type == SMEntry.type:
                output = False
        return output

    def remove_duplicates(self):
        # first, sort by location and by type...
        self._SMEntries = sorted(self._SMEntries, key= lambda x: (x.location, x.size), reverse=False)
        # remove duplicates base on type and location
        newSMEntries = []
        for entry in self._SMEntries:
            if self.no_SMEntry_duplicate_in(newSMEntries, entry):
                newSMEntries.append(entry)
        self._SMEntries = newSMEntries



    def mark_duplicates(self):
        self._SMEntries = sorted(self._SMEntries, key=StructPadder.compareLocations, reverse=False)
        pass

    def output_struct_template(self):
        pass



if __name__ == '__main__':
    inputFile = open("input", "r")
    line = inputFile.readline()
    memap = MemoryAccessProtocol(line) # parse meta information line
    while line != '':
        line = inputFile.readline()
        memap.parseline(line)
    memap.generate_member_entries()
    memap.output_struct_template()
