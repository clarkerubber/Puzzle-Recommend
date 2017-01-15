import chess
import chess.pgn
import operator
import pprint
from pymongo import MongoClient

try:
  from StringIO import StringIO
except ImportError:
  from io import StringIO

def update_structures(puzzleColl, p):
  board = chess.Board(p['fen'])
  puzzleColl.update_one({'_id': p['_id']}, {'$set': {'pawns': {'w': int(board.pieces(chess.PAWN, True)), 'b': int(board.pieces(chess.PAWN, False))}}}, upsert = True)

def similar_to(puzzleColl, board, pawns):
  related = puzzleColl.find({"_id": {"$gt": 61000}, "$or": [{"pawns.w": int(pawns['w'])}, {"pawns.b": int(pawns['b'])}], "vote.enabled": True})
  similar = []
  for i in related:
    b = chess.Board(i['fen'])
    # another bitwise XOR but this time more robust
    dif = len(pawns['w'] ^ b.pieces(chess.PAWN, True)) + len(pawns['b'] ^ b.pieces(chess.PAWN, False))
    i['difference'] = dif
    if dif < 5:
      similar.append(i)
      if len(similar) > 3:
        break
  return sorted(similar, key=lambda x: x['difference'])[:4]

def recommend(pgn_string):
  pgn = StringIO(pgn_string)
  game = chess.pgn.read_game(pgn)
  node = game

  boards = []
  unique_pawns = []
  while not node.is_end():
    next_node = node.variation(0)
    move_num = node.board().fullmove_number
    if move_num > 7:
      pawns = {'w': node.board().pieces(chess.PAWN, True), 'b': node.board().pieces(chess.PAWN, False)}
      if len(pawns['w']) + len(pawns['b']) < 10:
        break
      if pawns not in unique_pawns:
        unique_pawns.append(pawns)
        boards.append(node.board())
    node = next_node

  similar = []
  for b, p in zip(boards, unique_pawns):
    s = similar_to(puzzleColl, b, p)
    similar.extend(s)
    
  max_dif = max([i['difference'] for i in sorted(similar, key=lambda x: x['difference'])[:20]])
  unique_ordered = []
  for p in similar:
    if p['_id'] not in unique_ordered and p['difference'] <= max_dif:
      unique_ordered.append(p)
  return unique_ordered


client = MongoClient()
db = client.lichess
puzzleColl = db.puzzle

#update puzzleColl for indexing
#for p in puzzleColl.find({"_id": {"$gt": 61000}}):
#  update_structures(puzzleColl, p)

# game we're finding related puzzles to
pgn_string = """
[Event "Rated game"]
[Site "https://lichess.org/ixfpCQce"]
[Date "2017.01.15"]
[White "gromov"]
[Black "thibault"]
[Result "1-0"]
[WhiteElo "1486"]
[BlackElo "1609"]
[PlyCount "59"]
[Variant "Standard"]
[TimeControl "60+0"]
[ECO "A06"]
[Opening "Reti Opening"]
[Termination "Normal"]
[Annotator "lichess.org"]

1. Nf3 d5 { A06 Reti Opening } 2. Ne5 c5 3. Nxf7 Kxf7 4. e4 Ke8 5. e5 Nc6 6. c3 Nxe5 7. d4 cxd4 8. cxd4 Nc6 9. Bb5 Nf6 10. O-O Bd7 11. Nc3 a6 12. Bd3 b5 13. Bg5 Nxd4 14. Bxf6 exf6 15. Nxd5 Be7 16. Nxe7 Qxe7 17. Re1 Qxe1+ 18. Qxe1+ Kf7 19. Rd1 Rhe8 20. Qd2 Rac8 21. Bxh7 Nf3+ 22. gxf3 Be6 23. Qd6 Rcd8 24. Qc7+ Rd7 25. Rxd7+ Kf8 26. Rxg7 Rc8 27. Rg8+ Bxg8 28. Qxc8+ Kg7 29. Qxg8+ Kh6 30. Qg6# { Black is checkmated } 1-0
"""

from datetime import datetime
startTime = datetime.now()

pprint.pprint(["https://en.lichess.org/training/"+str(i['_id']) for i in recommend(pgn_string)])

print datetime.now() - startTime