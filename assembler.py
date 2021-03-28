class Assembler(object):
    def __init__(self, asmpath='', mripath='', rripath='', ioipath='') -> None:
        """
        Assembler class constructor.
        Initializes 7 important properties of the Assembler class:
        -   self.__address_symbol_table (dict): stores labels (scanned in the first pass)
            as keys and their locations as values.
        -   self.__bin (dict): stores locations (or addresses) as keys and the binary 
            representations of the instructions at these locations (job of the second pass) 
            as values.
        -   self.__asmfile (str): the file name of the assembly code file. This property
            is initialized and defined in the read_code() method.
        -   self.__asm (list): list of lists, where each outer list represents one line of 
            assembly code and the inner list is a list of the symbols in that line.
            for example:
                ORG 100
                CLE
            will yiels __asm = [['org', '100'] , ['cle']]
            Notice that all symbols in self.__asm are in lower case.
        -   self.__mri_table (dict): stores memory-reference instructions as keys, and their
            binary representations as values.
        -   self.__rri_table (dict): stores register-reference instructions as keys, and their
            binary representations as values.
        -   self.__ioi_table (dict): stores input-output instructions as keys, and their
            binary representations as values.
        
        Thie constructor receives four optional arguments:
        -   asmpath (str): path to the assembly code file.
        -   mripath (str): path to text file containing the MRI instructions. The file should
            include each intruction and its binary representation separated by a space in a
            separate line. Their must be no empty lines in this file.
        -   rripath (str): path to text file containing the RRI instructions. The file should
            include each intruction and its binary representation separated by a space in a
            separate line. Their must be no empty lines in this file.
        -   ioipath (str): path to text file containing the IOI instructions. The file should
            include each intruction and its binary representation separated by a space in a
            separate line. Their must be no empty lines in this file.
        """
        super().__init__()
        # Address symbol table dict -> {symbol: location}
        self.__address_symbol_table = {}
        # Assembled machine code dict -> {location: binary representation}
        self.__bin = {}
        # Load assembly code if the asmpath argument was provided.
        if asmpath:
            self.read_code(asmpath)
            # memory-reference instructions
        self.__mri_table = self.__load_table(mripath) if mripath else {}
        # register-reference instructions
        self.__rri_table = self.__load_table(rripath) if rripath else {}
        # input-output instructions
        self.__ioi_table = self.__load_table(ioipath) if ioipath else {}

    def read_code(self, path='testcode.asm'):
        """
        opens .asm file found in path and stores it in self.__asmfile.
        Returns None
        """
        assert path.endswith('.asm') or path.endswith('.S'), \
            'file provided does not end with .asm or .S'
        self.__asmfile = path.split('/')[-1]  # on unix-like systems
        with open(path, 'r') as f:
            # remove '\n' from each line, convert it to lower case, and split
            # it by the whitespaces between the symbols in that line.
            self.__asm = [s.rstrip().lower().split() for s in f.readlines()]

    def assemble(self, inp='') -> dict:
        assert self.__asm or inp, 'no assembly file provided'
        if inp:
            assert inp.endswith('.asm') or inp.endswith('.S'), \
                'file provided does not end with .asm or .S'
        # if assembly file was not loaded, load it.
        if not self.__asm:
            self.read_code(inp)
        # remove comments from loaded assembly code.
        self.__rm_comments()
        # do first pass.
        self.__first_pass()
        # do second pass.
        self.__second_pass()
        # The previous two calls should store the assembled binary
        # code inside self.__bin. So the final step is to return
        # self.__bin
        return self.__bin
    # PRIVATE METHODS
    def __load_table(self, path) -> dict:
        """
        loads any of ISA tables (MRI, RRI, IOI)
        """
        with open(path, 'r') as f:
            t = [s.rstrip().lower().split() for s in f.readlines()]
        return {opcode: binary for opcode, binary in t}

    def __islabel(self, string) -> bool:
        """
        returns True if string is a label (ends with ,) otherwise False
        """
        return string.endswith(',')

    def __rm_comments(self) -> None:
        """
        remove comments from code
        """
        for i in range(len(self.__asm)):
            for j in range(len(self.__asm[i])):
                if self.__asm[i][j].startswith('/'):
                    del self.__asm[i][j:]
                    break

    def __format2bin(self, num: str, numformat: str, format_bits: int) -> str:
        """
        converts num from numformat (hex or dec) to binary representation with
        max format_bits. If the number after conversion is less than format_bits
        long, the formatted text will be left-padded with zeros.
        Arguments:
            num (str): the number to be formatted as binary. It can be in either
                        decimal or hexadecimal format.
            numformat (str): the format of num; either 'hex' or 'dec'.
            format_bits (int): the number of bits you want num to be converted to
        """
        if numformat == 'dec':
            return '{:b}'.format(int(num)).zfill(format_bits)
        elif numformat == 'hex':
            return '{:b}'.format(int(num, 16)).zfill(format_bits)
        else:
            raise Exception('format2bin: not supported format provided.')

    def __first_pass(self) -> None:
        """
        Runs the first pass over the assmebly code in self.__asm.
        Should search for labels, and store the labels alongside their locations in
        self.__address_symbol_table. The location must be in binary (not hex or dec).
        Returns None
        """
        linecounter=0
        inc = 0  # my counter
        org = self.__asm[0][1]  # take first number of org to start indexing
        for i in range(1, len(self.__asm) - 1):  # no need to include either first org
            if self.__asm[i][0] == 'end':
                break
            if self.__asm[i][0] == 'org':  # in case another org occurs reset counter and set new org
                org = self.__asm[i][1]
                inc = -1
            linecounter+=1
            ctr = self.__format2bin(hex(int(org, 16) + inc)[2::], 'hex', 12)
            inc += 1
            if self.__islabel(self.__asm[i][0]):  # in case input is label
                assert len(self.__asm[
                               i]) >= 2, "Invalid Assembly Code, in line {}".format(linecounter+1)  # assert if label not followed by instruction and halt the entire assembler
                self.__address_symbol_table[self.__asm[i][0]] = ctr  # if there is an instruction column act as usual
            self.__bin[ctr] = None  # set bin dict values to none as I iterate and set ctr as key for every iteration

    def __second_pass(self) -> None:
        """
        Runs the second pass on the code in self.__asm.
        Should translate every instruction into its binary representation using
        the tables self.__mri_table, self.__rri_table and self.__ioi_table. It should
        also store the translated instruction's binary representation alongside its 
        location (in binary too) in self.__bin.
        """
        flag = False
        for i in range(1, len(self.__asm) - 1):
            if self.__asm[i][0] == 'end':
                break
            elif 'hlt' in self.__asm[i]:  # if hlt exist then convert every value in-front of label to binary
                self.__bin[list(self.__bin.keys())[i - 1]] = self.__rri_table['hlt']
                flag = True
            elif self.__asm[i][0] in self.__rri_table.keys():  # if label does not exist in rri instruction
                self.__bin[list(self.__bin.keys())[i - 1]] = self.__rri_table[self.__asm[i][0]]
            elif self.__asm[i][1] in self.__rri_table.keys():  # if label exist before rri instruction
                self.__bin[list(self.__bin.keys())[i - 1]] = self.__rri_table[self.__asm[i][1]]
            elif self.__asm[i][0] in self.__mri_table.keys():  # if label does not exist in mri instruction
                if 'i' in self.__asm[i][1::]:  # direct/indirect mode
                    I = '1'
                else:
                    I = '0'
                self.__bin[list(self.__bin.keys())[i - 1]] = I + self.__mri_table[self.__asm[i][0]] + \
                                                             self.__address_symbol_table[self.__asm[i][1] + ',']
            elif self.__asm[i][1] in self.__mri_table.keys():  # if label exist in mri instruction
                if 'i' in self.__asm[i][1::]:
                    I = '1'
                else:
                    I = '0'
                self.__bin[list(self.__bin.keys())[i - 1]] = I + self.__mri_table[self.__asm[i][1]] + \
                                                             self.__address_symbol_table[self.__asm[i][2] + ',']
            elif self.__asm[i][0] in self.__ioi_table.keys():  # if label does not exist in ioi instruction
                self.__bin[list(self.__bin.keys())[i - 1]] = self.__ioi_table[self.__asm[i][0]]
            elif self.__asm[i][1] in self.__ioi_table.keys():  # if label exist in ioi instruction
                self.__bin[list(self.__bin.keys())[i - 1]] = self.__ioi_table[self.__asm[i][1]]
            elif self.__islabel(self.__asm[i][0]) and flag:  # if label exist after HLT
                if self.__asm[i][1] == 'hex':  # if type is hex convert to binary
                    self.__bin[list(self.__bin.keys())[i - 1]] = self.__format2bin(self.__asm[i][2], 'hex', 16)
                elif self.__asm[i][1] == 'dec':  # if type is dec convert to binary
                    self.__bin[list(self.__bin.keys())[i - 1]] = self.__format2bin(self.__asm[i][2], 'dec', 16)
                else:
                    print('error')
        dv = list(self.__bin.values())
        dk = list(self.__bin.keys())
        for i in range(len(dv)):  # delete some redundant value from bin dict
            if dv[i] == None:
                self.__bin.pop(dk[i])
