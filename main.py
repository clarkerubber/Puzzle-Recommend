import chess
import chess.pgn
import operator
import pprint
from pymongo import MongoClient

def update_structures(puzzleColl, p):
  board = chess.Board(p['fen'])
  puzzleColl.update_one({'_id': p['_id']}, {'$set': {'w_pawns': int(board.pieces(chess.PAWN, True)), 'b_pawns': int(board.pieces(chess.PAWN, False))}}, upsert = True)

def similar_to(puzzleColl, board):
  # bitwise XOR on pawn positions (not perfect but effective)
  where = "(this.w_pawns ^ %s).toString(2).split('').concat((this.b_pawns ^ %s).toString(2).split('')).reduce(function(a, b){return (parseInt(a) || 0) + (parseInt(b) || 0)}) <= 1" % (int(board.pieces(chess.PAWN, True)), int(board.pieces(chess.PAWN, False)))
  print where
  related = puzzleColl.find({"_id": {"$gt": 61000}, "$where": where})
  similar = []
  for i in related[:100]:
    b = chess.Board(i['fen'])
    # another bitwise XOR but this time more robust
    i['difference'] = len(board.pieces(chess.PAWN, True) ^ b.pieces(chess.PAWN, True)) + len(board.pieces(chess.PAWN, False) ^ b.pieces(chess.PAWN, False))
    similar.append(i)

  similar = sorted(similar, key=lambda x: x['difference'])
  if len(similar) > 0:
    print ' '
    print "%s puzzles related to %s" % (len(similar), board.fen())
  for i in similar[:3]:
    print 'https://en.lichess.org/training/'+str(i['_id']) + ' : ' + str(i['difference'])


client = MongoClient()
db = client.lichess
puzzleColl = db.puzzle

#update puzzleColl for indexing
#for p in puzzleColl.find({"_id": {"$gt": 61000}}):
  #update_structures(puzzleColl, p)

# game we're finding related puzzles to
pgn_string = """
[Event "Casual game"]
[Site "https://lichess.org/Fr1cBAaq"]
[Date "2017.01.07"]
[White "kluis"]
[Black "amazingoid"]
[Result "0-1"]
[WhiteElo "1930"]
[BlackElo "2603"]
[PlyCount "40"]
[Variant "Standard"]
[TimeControl "180+0"]
[ECO "B34"]
[Opening "Sicilian Defense: Accelerated Dragon, Exchange Variation"]
[Termination "Normal"]
[Annotator "lichess.org"]

1. e4 c5 2. Nf3 Nc6 3. d4 cxd4 4. Nxd4 g6 5. Nxc6 { B34 Sicilian Defense: Accelerated Dragon, Exchange Variation } bxc6 6. c3 Bg7 7. Bg5 Nf6 8. Bxf6 Bxf6 9. Nd2 Rb8 10. Qc2 Qb6 11. Rb1 O-O 12. Bc4 Rd8 13. Bb3 Ba6 14. Nc4 Qc5 15. Nd2 d5 16. f4 Qe3+ 17. Kd1 dxe4 18. Re1 Qxf4 19. c4 e3 20. Rf1 Qxf1# { White is checkmated } 0-1
"""


try:
  from StringIO import StringIO
except ImportError:
  from io import StringIO

pgn = StringIO(pgn_string)
game = chess.pgn.read_game(pgn)
node = game

boards = []
unique_pawns = []
while not node.is_end():
  next_node = node.variation(0)

  if node.board().fullmove_number > 5:
    pawns = {'w': node.board().pieces(chess.PAWN, True), 'b': node.board().pieces(chess.PAWN, False)}
    if pawns not in unique_pawns:
      unique_pawns.append(pawns)
      boards.append(node.board())
  node = next_node

for b in boards:
  similar_to(puzzleColl, b)