import numpy as np
import json

BUFFERS = {
    "corner": ["UFR", "UFL", "UBR", "UBL", "DFR", "DFL", "DBL", "DBR"],
    "edge": ["UF", "UR", "UB", "UL", "FR", "FL", "DF", "DB", "DR", "DL", "BR", "BL"]
}

# piece.py

class Piece():
    def __init__(self, x, y, z):
        xd = {0: "L", 1: "", 2: "R"}
        yd = {0: "D", 1: "", 2: "U"}
        zd = {0: "F", 1: "", 2: "B"}
        self.sides = [xd[x], yd[y], zd[z]]

    def get_name(self, axis=1):
        face_precedence = {"U": 0, "D": 0, "F": 1, "B": 1, "R": 2, "L": 2, "": 3}
        axis_face = self.sides[axis]
        axis_face = self.sides[2] if not axis_face else axis_face
        name = self.sides.copy()
        index = name.index(axis_face)
        name[index], name[0] = name[0], name[index]
        name[1:] = sorted(name[1:], key=lambda x: face_precedence[x])
        return "".join(name)
                
    def swap_stickers(self, axis1, axis2):
        self.sides[axis1], self.sides[axis2] = self.sides[axis2], self.sides[axis1]
        return
    
    def roll(self, k):
        self.sides = np.roll(self.sides, k)
        return

# cube.py

FACES = {
    "L": {"axis": 0, "pos": 0},
    "M": {"axis": 0, "pos": 1},
    "R": {"axis": 0, "pos": 2},
    "F": {"axis": 2, "pos": 0},
    "S": {"axis": 2, "pos": 1},
    "B": {"axis": 2, "pos": 2},
    "U": {"axis": 1, "pos": 2},
    "E": {"axis": 1, "pos": 1},
    "D": {"axis": 1, "pos": 0}
}

class Cube():
    def __init__(self):
        self.cube = np.ndarray((3, 3, 3), dtype=Piece)
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    self.cube[x, y, z] = Piece(x, y, z)

        self.solved = np.copy(self.cube)
        self.scramble = ""

    def reset_cube_to_solved(self):
        self.cube = self.solved
        return

    def single_turn(self, face, clockwise=True):
        k = 1 if clockwise else -1
        k = -k if face in {"U", "L", "F", "S", "M"} else k
        axis, pos = FACES[face].values()
        index = [slice(None), slice(None), slice(None)]
        index[axis] = pos
        index = tuple(index)
        self.cube[index] = np.rot90(self.cube[index], k)
        axis1, axis2 = {0, 1, 2} - {axis}
        for piece in self.cube[index].flatten():
            piece.swap_stickers(axis1, axis2)
        return

    def wide_turn(self, face, clockwise=True):
        sliceclockwise = clockwise
        if face in {"R", "U", "B"}:
            sliceclockwise = not clockwise
        if face in {"L", "R"}:
            sliceface = "M"
        elif face in {"U", "D"}:
            sliceface = "E"
        elif face in {"F", "B"}:
            sliceface = "S"
        self.single_turn(face, clockwise)
        self.single_turn(sliceface, sliceclockwise)
        return

    def rotation(self, rotation, clockwise=True):
        axis = rotation[0]
        if axis == "x":
            moves = ["R", "M'", "L'"]
        elif axis == "y":
            moves = ["U", "E'", "D'"]
        elif axis == "z":
            moves = ["F", "S", "B'"]
        
        if not clockwise:
            [[self.do_move(move) for move in moves] for i in range(3)]
        else:
            [self.do_move(move) for move in moves]
        return

    def do_move(self, move):
        if move[0] in "urfbld":
            move = move[0].upper() + "w" + move[1:]
            self.do_move(move)
            # print(move)
            return
            
        clockwise = False if "'" in move else True
        face = move[0]
        turn = lambda x: self.single_turn(face, clockwise)
        if "x" in move or "y" in move or "z" in move:
            turn = lambda x: self.rotation(face, clockwise)
        if "w" in move:
            turn = lambda x: self.wide_turn(face, clockwise)
        if "2" in move:
            turn(face)
            turn(face)
        else:
            turn(face)
        return


    def get_coords(self, p):
        d = {FACES[x]['axis']: FACES[x]['pos'] for x in p}
        for i in [0, 1, 2]:
            if i not in d.keys():
                d[i] = 1
        return (d[0], d[1], d[2])

    def pseudoswap(self, e1, e2):
        # HARDCODED UF UR FOR NOW
        self.cube[1,2,0].sides = ['', 'U', 'R']
        self.cube[2,2,1].sides = ['F', 'U', '']


        return

        c1, c2 = self.get_coords(e1), self.get_coords(e2)
        e11, e12 = list(e1)
        e21, e22 = list(e2)

        # TODO FIX THIS
        b1 = [x for x in self.cube[c1].sides if x][0]
        b2 = [x for x in self.cube[c2].sides if x][0]

        for i in range(3):
            if not self.cube[c1].sides[i]:
                s1 = i
                break
        for i in range(3):
            if not self.cube[c2].sides[i]:
                s2 = i
                break
        ns1 = sorted(list({0, 1, 2} - {s1}))
        print(ns1)
        ns2 = sorted(list({0, 1, 2} - {s2}))
        print(ns2)
        self.cube[c1].sides[ns1[0]], self.cube[c1].sides[ns1[1]] = e21, e22
        self.cube[c2].sides[ns2[0]], self.cube[c2].sides[ns2[1]] = e11, e12

        return


    def scramble_from_string(self, scram):
        self.scramble = scram
        moves = scram.split(" ")
        for move in moves:
            self.do_move(move)
        return
    
# tracer.py

class Tracer(Cube):
    def __init__(self, buffers, trace="both"):
        super().__init__()
        self.tracing = {"edge": [], "corner": []}
        self.buffers = buffers
        self.loopcube = []
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    self.loopcube.append((x, y, z))
    
        self.trace_corners = True if trace in {"corners", "both"} else False
        self.trace_edges = True if trace in {"edges", "both"} else False

    def find_piece(self, piecename):
        piecename = set(piecename)
        piece = [pos for pos in self.loopcube
                 if set(self.cube[pos].get_name()) == piecename][0]
        return piece

    def rotate_into_orientation(self):
        rotations = []
        u_center = self.find_piece("U")
        direction = max(set(u_center) - {1})
        axis = u_center.index(direction)
        if axis == 2:
            rotation = "x" if direction == 0 else "x'"
        elif axis == 0:
            rotation = "z" if direction == 0 else "z'"
        elif axis == 1:
            rotation = "z2" if direction == 0 else None
      
        if rotation:
            self.do_move(rotation)
            rotations.append(rotation)

        f_center = self.find_piece("F")
        direction = max(set(f_center) - {1})
        axis = f_center.index(direction)
        if axis == 2:
            rotation = None if direction == 0 else "y2"
        elif axis == 0:
            rotation = "y" if direction == 2 else "y'"

        if rotation:
            self.do_move(rotation)
            rotations.append(rotation)
         
        self.tracing["rotation"] = rotations

        return
    
    def coords_from_name(self, name):
        coords = [1, 1, 1]
        for side in name:
            if side == "F":
                coords[2] = 0
            elif side == "B":
                coords[2] = 2
            elif side == "U":
                coords[1] = 2
            elif side == "D":
                coords[1] = 0
            elif side == "R":
                coords[0] = 2
            elif side == "L":
                coords[0] = 0
        return tuple(coords)   
    
    def where_to(self, a):
        axis = FACES[a[0]]["axis"]
        piece = self.coords_from_name(a)
        return self.cube[piece].get_name(axis=axis)
    
    def set_buffer(self, target):
        self.buffer = target
        return
    
    def trace_from_target(self, target, targets=None):
        targets = targets if targets else []
        to = self.where_to(target)
        if set(list(to)) == set(list(self.buffer)):
            return
        else:
            targets.append(to)
            self.trace_from_target(to, targets)
        return targets
    
    def absolute_target(self, target):
        return set(list(target))
    
    def find_flips(self):
        flips = []
        for piece in self.loopcube:
            x, y, z = piece
            name = Piece(x, y, z).get_name()
            to_name = self.cube[piece].get_name()
            if 1 in piece \
            and set(list(name)) == set(list(to_name)) \
            and name != to_name:
                flips.append(name)
        return flips
    
    def find_twists(self):
        twists = []
        for piece in self.loopcube:
            x, y, z = piece
            name = Piece(x, y, z).get_name()
            to_name = self.cube[piece].get_name()
            if 1 not in piece \
            and set(list(name)) == set(list(to_name)) \
            and name != to_name:
                abs_target = set(list(name))
                from_sticker = name[0]
                to_sticker = to_name[0]
                
                if to_sticker in {"R", "L"} and from_sticker in {"U", "D"}:
                    ori = 1
                elif to_sticker in {"F", "B"} and from_sticker in {"U", "D"}:
                    ori = -1
                elif to_sticker in {"U", "D"} and from_sticker in {"F", "B"}:
                    ori = 1
                elif to_sticker in {"R", "L"} and from_sticker in {"F", "B"}:
                    ori = -1
                elif to_sticker in {"U", "D"} and from_sticker in {"R", "L"}:
                    ori = 1
                elif to_sticker in {"F", "B"} and from_sticker in {"R", "L"}:
                    ori = -1

                if abs_target in [{"U", "F", "R"}, {"U", "B", "L"}, {"D", "B", "R"}, {"D", "F", "L"}]:
                    ori = -ori        
                    
                twists.append({"location": name, "orientation": ori})
        return twists
                
                                                                                                   
    def edge_cycle_ori(self, targets):
        return 0 if self.where_to(targets[-1]) == self.buffer else 1

    def corner_cycle_ori(self, targets):
        last_target = self.where_to(targets[-1])
        abs_target = set(list(last_target))
        last_sticker = last_target[0]
        buffer_sticker = self.buffer[0]
        if last_target == self.buffer:
            return 0
        if last_sticker in {"R", "L"} and buffer_sticker in {"U", "D"}:
            ori = 1
        elif last_sticker in {"F", "B"} and buffer_sticker in {"U", "D"}:
            ori = -1
        elif last_sticker in {"U", "D"} and buffer_sticker in {"F", "B"}:
            ori = 1
        elif last_sticker in {"R", "L"} and buffer_sticker in {"F", "B"}:
            ori = -1
        elif last_sticker in {"U", "D"} and buffer_sticker in {"R", "L"}:
            ori = 1
        elif last_sticker in {"F", "B"} and buffer_sticker in {"R", "L"}:
            ori = -1
            
        if abs_target in [{"U", "F", "R"}, {"U", "B", "L"}, {"D", "B", "R"}, {"D", "F", "L"}]:
            ori = -ori
    
        return ori
    
    def cycle_parity(self, targets):
        return 1 if len(targets) % 2 else 0
   

    def trace_all(self, piecetype, buffers):
        solved = []
        for buffer in buffers:
            if self.absolute_target(buffer) in [self.absolute_target(x) for x in solved]:
                continue
            self.set_buffer(buffer)
            targets = self.trace_from_target(buffer)
            if targets:
                [solved.append(target) for target in targets]
                parity = self.cycle_parity(targets)
                ori = self.edge_cycle_ori(targets) if piecetype == "edge" else self.corner_cycle_ori(targets)
                self.tracing[piecetype].append({"type": "cycle", "buffer": buffer, "targets": targets, "orientation": ori, "parity": parity})

        if piecetype == "edge":
            flips = self.find_flips()
            if flips:
                for flip in flips:
                    self.tracing["edge"].append({"type": "misoriented", "buffer": flip, "targets": [], "orientation": 1, "parity": 0})
                    
        elif piecetype == "corner":
            twists = self.find_twists()
            if twists:
                for twist in twists:
                    self.tracing["corner"].append({"type": "misoriented", "buffer": twist["location"], "targets": [], "orientation": twist["orientation"], "parity": 0})

        return
    
    def modify_buffer_order(self, edgebuffers, cornerbuffers):
        self.buffers["edge"] = edgebuffers
        self.buffers["corner"] = cornerbuffers
        return

    def manual_swap(self, e1, e2):
        # CURRENTLY ONLY SUPPORTS PSEUDOSWAPS PRESERVING F/B EO
        coords1, coords2 = self.coords_from_name(e1), self.coords_from_name(e2)
        slice1, slice2 = self.cube[coords1].sides.index(''), self.cube[coords2].sides.index('')
        non_slice1, non_slice2 = sorted(list({0, 1, 2} - {slice1})), sorted(list({0, 1, 2} - {slice2}))
        piece1, piece2 = [f for f in self.cube[coords1].sides if f], [f for f in self.cube[coords2].sides if f]
        # idk why you have to do this but it works
        if sorted([slice1, slice2]) == [0, 1] or sorted([slice1, slice2]) == [0, 2]:
            piece2 = reversed(piece2)
            piece1 = reversed(piece1)

        self.cube[coords1].sides[non_slice1[0]], self.cube[coords1].sides[non_slice1[1]] = piece2
        self.cube[coords2].sides[non_slice2[0]], self.cube[coords2].sides[non_slice2[1]] = piece1
        return

    def sort_tracing(self):
        self.tracing["edge"].sort(key=lambda x: self.buffers["edge"].index(x["buffer"]))
        self.tracing["corner"].sort(key=lambda x: self.buffers["corner"].index(x["buffer"]))

    def trace_cube(self):
        self.tracing = {"edge": [], "corner": [], "scramble": self.scramble}
        self.rotate_into_orientation()
        if self.trace_corners:
            self.trace_all("corner", self.buffers["corner"])
        if self.trace_edges:
            self.trace_all("edge", self.buffers["edge"])
        self.sort_tracing()
        return