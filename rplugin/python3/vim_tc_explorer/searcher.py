# ============================================================================
# FILE: searcher.py
# AUTHOR: Philip Karlsson <philipkarlsson at me.com>
# License: MIT license
# ============================================================================
import os
from vim_tc_explorer.filter import filter


class resultGroup(object):
    def __init__(self, fileName):
        self.lines = []
        self.matches = 0
        self.fileName = fileName


class searcher(object):
    def __init__(self, nvim, buffer, cwd):
        self.nvim = nvim
        self.filter = filter()
        self.buffer = buffer
        # Attribute to distinguish from explorer
        self.isSearcher = True
        self.selected = 0
        self.fileredFiles = []
        self.expanded = False
        self.cwd = cwd
        # Header takes up 6 rows
        self.headerLength = 6

    def assignBuffer(self, buffer):
        # This method is only called during re-init so we already have old
        # results
        self.buffer = buffer
        self.prevbuffer = self.nvim.current.buffer
        self.nvim.current.buffer = self.buffer
        self.nvim.command('setlocal filetype=vim_tc_search_result')
        self.nvim.current.buffer = self.prevbuffer
        # self.createResultStructure()
        # self.draw()

    def createResultStructure(self):
        self.results = {}
        self.resultFiles = []
        for line in self.buffer[1:len(self.buffer)]:
            # Process each line
            f = line.split(':')
            if(f is not None):
                if(not f[0] in self.results):
                    self.results[f[0]] = resultGroup(f[0])
                    self.resultFiles.append(f[0])
                self.results[f[0]].lines.append(line)
                self.results[f[0]].matches += 1

    def getFileListFromResults(self):
        self.fileList = []
        self.rawFileList = []
        for res in self.fileredFiles:
            # Add the file
            self.rawFileList.append(res)
            self.fileList.append('+'+res + ' | ' +
                                 str(self.results[res].matches) + ' matches')
            if self.expanded:
                for l in self.results[res].lines:
                    self.fileList.append('  -'+l)
                    self.rawFileList.append(l)

    def search(self, dir, filePattern, inputPattern):
        self.prevbuffer = self.nvim.current.buffer
        self.nvim.current.buffer = self.buffer
        self.nvim.command('setlocal filetype=vim_tc_search_result')
        self.dir = dir
        self.inputPattern = inputPattern
        self.filePattern = filePattern
        self.command = "cd %s && " % dir
        if(not filePattern.startswith('-')):
                filePattern = '-t' + filePattern
        if(inputPattern is not ''):
            self.command += "rg %s %s --vimgrep" % (filePattern, inputPattern)
        else:
            filePattern = filePattern.replace('-t', '-g')
            self.command += "rg %s --files" % (filePattern)
        self.buffer[:] = []
        self.nvim.command("r !%s" % self.command)
        self.nvim.current.buffer = self.prevbuffer
        self.createResultStructure()
        self.getFileListFromResults()

    def find(self, dir, pattern):
        self.prevbuffer = self.nvim.current.buffer
        self.nvim.current.buffer = self.buffer
        self.nvim.command('setlocal filetype=vim_tc_search_result')
        self.dir = dir
        self.command = "cd %s && " % dir
        self.command += "rg -g *%s* --files" % (pattern)
        self.buffer[:] = []
        self.nvim.command("r !%s" % self.command)
        self.nvim.current.buffer = self.prevbuffer
        self.createResultStructure()
        self.getFileListFromResults()

    def grep(self, dir, filePattern, pattern):
        self.prevbuffer = self.nvim.current.buffer
        self.nvim.current.buffer = self.buffer
        self.nvim.command('setlocal filetype=vim_tc_search_result')
        self.dir = dir
        self.command = "cd %s && " % dir
        if(filePattern is not ''):
            filePattern = '-t' + filePattern
        self.command += "rg %s %s --vimgrep" % (filePattern, pattern)
        self.buffer[:] = []
        self.nvim.command("r !%s" % self.command)
        self.nvim.current.buffer = self.prevbuffer
        self.createResultStructure()
        self.getFileListFromResults()

    def updateListing(self, pattern):
        self.filter.filter(self.resultFiles, pattern, self.fileredFiles)
        self.getFileListFromResults()
        self.changeSelection(0)

    def changeSelection(self, offset):
        # Selection is this time based on fileList
        self.selected += offset
        if self.selected < 0:
            self.selected = 0
        elif self.selected >= len(self.fileList):
            self.selected = len(self.fileList)-1

    def toggle(self):
        self.expanded = not self.expanded
        self.getFileListFromResults()

    def draw(self):
        self.buffer[:] = self.getUIHeader()
        # Draw each file
        for idx, val in enumerate(self.fileList):
            if idx == self.selected:
                token = '-->'
            else:
                token = '   '
            self.buffer.append(token + val)
        # Debug
        # self.buffer.append(self.command)

    def getSelected(self):
        lineNum = None
        currLine = self.rawFileList[self.selected]
        if(':' in currLine):
            # This is a match in a file
            lineParts = currLine.split(':')
            self.buffer[:] = lineParts
            pathToFile = os.path.join(self.cwd, lineParts[0])
            lineNum = int(lineParts[1])
        else:
            pathToFile = os.path.join(self.cwd, currLine)
        return pathToFile, lineNum

    def getUIHeader(self):
        bar = "==============================================================="
        leadingC = '#'
        ret = []
        ret.append(leadingC + bar)
        ret.append(leadingC + ' Bolt search results (%d results)' %
                   len(self.fileList))
        # Shall be highlighted
        ret.append(leadingC + '  $>' + self.command)
        qhStr = '  Quick Help: <Ret>:Open <C-a>:Expand <C-q>:Quit'
        ret.append(leadingC + qhStr)
        ret.append(leadingC + bar)
        return ret
