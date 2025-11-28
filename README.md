# 3-Style Execution Trainer

https://namisama269.github.io/3style-execution-trainer/

3-Style Execution Trainer is a tool for training the execution step of blindsolving by drilling 3-style comms, focusing on recall, transitioning between comms and cancellations.

You are given a sequence of 5 comms to solve for a piece type from your letter scheme and buffer, which when done from a solved cube will bring the cube back to solved, making drilling execution much more effective than having to scramble the cube. The sequence does not contain any trivial repeated or inverse comms.

<table>
  <tr>
    <td align="center">
      <img src="images/settings_screen.png?v=2025-11-28" alt="Settings screen" height="420" />
    </td>
    <td align="center">
      <img src="images/focus_screen.png?v=2025-11-28" alt="Focus screen" height="420" />
    </td>
  </tr>
</table>

## Settings

### Piece type

Select the type of piece to train. Select “Custom” for other piece types such as other puzzles like Megaminx/FTO.

### Method

Two methods are used to generate the comm sequence (see below). It is recommended to use 5-cycle.

### Randomize orientation

In the 5-cycle method, randomize the orientation of the third comm to add more variance. This setting must be turned off when the piece type is a center piece.

### Shift sequence

After a sequence that does not affect the cube state is generated, it can be shifted up and down any number of times while still remaining valid. This setting randomly shifts the sequence to add more variance. It is recommended to turn this on while using practice letter pairs in order to change the position of those letter pairs. However, keep in mind that turning this setting on may generate sequences where the cube will end up solved midway.

### Letter scheme

Scheme to define letters on each piece and the buffer floating order (see [below](#reference-scheme-in-speffz-with-standard-buffers-and-floating-order)).

### Buffer letter

Select the buffer to do comms from. Letters for the comms will be selected only from pieces later than the piece that the buffer is on.

### Practice letter pairs

Enter in letter pairs for the current piece type that you want to guarantee to show in the sequence in order to practise them. One of them will be randomly selected and forced to be in the sequence. Select “Include inverses” to also add the inverse comm to the pool.

## Creating letter scheme

List out pieces in floating buffer order. If not using floating then only need the buffer piece to be first.

For each piece, write the letter for the buffer sticker first, then the other stickers on that piece (if there is more than 1 orientation). For corners, make sure that the letters are in clockwise order e.g. for the UFL piece using UFL buffer put the letters in the order UFL-FUL-LUF.

For bigBLD center pieces, treat each face as a piece with all 4 centers on the same face in the same block. By default this means that the buffer can be any of the U face centers, to get comms from one buffer move that buffer to its own piece at the start (e.g. x-center Ufr buffer in Speffz would be C ABD EFGH…)

Put each piece separated by spaces. If there is only one orientation (e.g. wings), the spaces can be removed to leave only one string of letters.

## Reference scheme in Speffz with standard buffers and floating order:

- Edges: `CI AQ BM DE JP LF UK WS VO XG TN RH`
- Corners: `CMJ DIF BQN AER PVK GLU WOT XSH`
- Wings: `CABDEFGHIJKLMNOPQRSTUVWX`
- Centers: `ABCD EFGH IJKL MNOP QRST UVWX`

## Method explanations

### 5-cycle method:

Suppose we have 5 pieces `A,B,C,D,E` and our buffer is `A`. The goal is to find a sequence of five 3-cycles that when done in succession does not change the state, and does not contain any two cycles that are the same or an inverse of each other.

First, do two 3-cycles `A-B-C` and `A-D-E` to create a 5-cycle. The current tracing from the buffer `A` is `EDCB`.

Next, try to find a 3-cycle that leaves the state in a single 5-cycle away from being solved which can be easily traced, and the two 3-cycles required to solve it are not repeats/inverses.

There are 12 cases for the next 3-cycle. Brute-forcing all of them and tracing from `A` gives:

`BC`: repeat of `BC`  
`BD`: `CB` `ED` (inverse of `BC`)  
`BE`: `DC` `BE` (repeat of `BE`)  
`CB`: inverse of `BC`  
`CD`: `CE` `DB`  
`CE`: `DC` `EB`  
`DB`: floating `2e2e` (`B-C`, `D-E`)  
`DC`: `2e2e` (`A-B`, `D-E`)  
`DE`: repeat of `DE`  
`EB`: floating 3-cycle (`B-D-C`)  
`EC`: `2e2e` (`A-B`, `C-D`)  
`ED`: inverse of `DE`

Only 2 options work for the third 3-cycle: `A-C-D` and `A-C-E`.

To generate the cycles, randomly select 4 pieces that are all after the buffer piece and pick a random orientation on each of them to generate the 5-cycle. Then randomly select one of the 2 valid third cycle patterns and randomize its orientation if the setting selected. Then the simplest way to find the remaining two cycles is to do the first three on the starting state and trace the remaining single 5-cycle.

### Chain method:

Randomly generate a permutation of the letters on all pieces after the buffer piece using backtracking, so that each letter is covered once and no two consecutive letters are on the same piece.

Then chain them so that the second letter on the previous 3-cycle becomes the first letter on the next 3-cycle, and the second letter on the last cycle matches the first letter of the first cycle.

This method allows generating sequences of up to as long as the number of letters, but is not recommended to use because the possible consecutive cycles are very restricted, making it not practical to practise cancellations and transition between comms.
