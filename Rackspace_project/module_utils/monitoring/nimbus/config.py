import re
import copy

class NimbusConfig(object):
    """
    Nimbus cluster config parser and manipulator. Expects section opening closing tags of the
    sections on separate lines and no duplicate sections.
    """

    class ParseError(Exception):
        pass

    def __init__(self):
        self._dict = {}

    def parse(self, fname):
        stack = []

        def setval(key, val):
            group = self._dict
            for sec in stack:
                group = group[sec]
            if key in group:
                raise self.ParseError("Duplicate key '%s -> %s'" % (' -> '.join(stack), key))
            group[key] = val

        def section(marker):
            # end section
            if marker.startswith('</'):
                sec_name = marker[2:-1]
                if not stack:
                    raise self.ParseError("Unmatched closing tag: %s" % sec_name)
                current_sec = stack.pop()
                if sec_name != current_sec:
                    raise self.ParseError("Opening/closing tags mismatch (%s/%s)" %
                                          (current_sec, sec_name))
            # start section
            else:
                sec_name = marker[1:-1]
                setval(sec_name, {})
                stack.append(sec_name)
        
        #installed.pkg is sometimes ISO-8859 instead of utf8, thus need this handling
        try:
            with open(fname) as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(fname, encoding='latin-1') as f:
                lines = f.readlines()

        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                continue
            elif line.startswith('<'):
                section(line)
                pass
            elif '=' in line:
                key, val = [x.strip() for x in line.split('=', 1)]
                setval(key, val)

    def write(self, fname=None):
        def write_section(f, sec_dict, indent):
            for key in sec_dict:
                if isinstance(sec_dict[key], dict):
                    f.write('%s<%s>\n' % (indent*' ', key))
                    write_section(f, sec_dict[key], indent+3)
                    f.write('%s</%s>\n' % (indent*' ', key))
                else:
                    f.write('%s%s = %s\n' % (indent * ' ', key, sec_dict[key]))

        f = open(fname, 'w')
        write_section(f, self._dict, 0)
        f.close()

    def update(self, update_dict):
        """
        Update the config with values from the provided dictionary. Return True if any
        changes were made, False otherwise
        """
        def deep_update(d, u):
            ch = False
            for k, v in u.iteritems():
                if isinstance(v, dict):
                    if k not in d:
                        d[k] = {}
                        ch = True
                    dch = deep_update(d[k], v)
                    ch = ch or dch
                else:
                    if k not in d or d[k] != u[k]:
                        ch = True
                    d[k] = u[k]
            return ch

        self._orig_dict = copy.deepcopy(self._dict)
        return deep_update(self._dict, update_dict)

    def remove(self, remove_list):
        """
        Remove certain options/sections from the config.

        Each item of the remove_list is a single  path to be removed. A path is a sequence
        of regular expressions matched against the corresponding level of the config tree. All
        branches matching the last regex in sequence are removed.
        """
        self._orig_dict = copy.deepcopy(self._dict)
        ch = False
        for path in remove_list:
            branches = [self._dict]
            for component in path[:-1]:
                newlevel = []
                for branch in branches:
                    for key in branch:
                        if re.match(component, key) is not None:
                            newlevel.append(branch[key])
                branches = newlevel

            for branch in branches:
                for key in branch.keys():
                    if re.match(path[-1], key) is not None:
                        ch = True
                        del branch[key]
        return ch

    def diff(self, fromdict=None):
        """
        Generate changes report in a human readable, diff-like style
        """
        if fromdict is None:
            if hasattr(self, '_orig_dict'):
                fromdict = self._orig_dict
            else:
                return None

        stack = []
        self._diff_stackpos = 0
        ret = []

        def sec_open(sign=' '):
            for tag in stack[self._diff_stackpos:]:
                ret.append('%s %s<%s>' % (sign, '  '*self._diff_stackpos, tag))
                self._diff_stackpos += 1

        def sec_close(sign=' '):
            tag = stack.pop()
            if self._diff_stackpos > len(stack):
                self._diff_stackpos -= 1
                ret.append('%s %s</%s>' % (sign, '  '*self._diff_stackpos, tag))

        def print_oneside(section, key, sign=' '):
            sec_open(sign)
            if isinstance(section[key], dict):
                stack.append(key)
                for k in sorted(section[key].keys()):
                    print_oneside(section[key], k, sign)
                sec_close(sign)
            else:
                ret.append('%s %s%s = %s' % (sign, '  '*self._diff_stackpos, key, section[key]))

        def print_update(orig, new, key):
            sec_open()
            ret.append('- %s%s = %s' % ('  '*self._diff_stackpos, key, orig[key]))
            ret.append('+ %s%s = %s' % ('  '*self._diff_stackpos, key, new[key]))

        def dictdiff(orig, new):
            for key in sorted(set(orig.keys() + new.keys())):
                if key not in orig:
                    sec_open()
                    print_oneside(new, key, '+')
                elif key not in new:
                    sec_open()
                    print_oneside(orig, key, '-')
                elif isinstance(new[key], dict):
                    stack.append(key)
                    dictdiff(orig[key], new[key])
                    sec_close()
                elif orig[key] != new[key]:
                    print_update(orig, new, key)

        dictdiff(fromdict, self._dict)
        return '\n'.join(ret)

    def facts(self):
        return self._dict
