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

def similar_to(puzzleColl, board):
  # bitwise XOR on pawn positions (not perfect but effective)
  where = "(this.pawns.w ^ %s).toString(2).split('').concat((this.pawns.b ^ %s).toString(2).split('')).reduce(function(a, b){return (parseInt(a) || 0) + (parseInt(b) || 0)}) == 1" % (int(board.pieces(chess.PAWN, True)), int(board.pieces(chess.PAWN, False)))
  related = puzzleColl.find({"_id": {"$gt": 61000}, "$where": where, "vote.enabled": True})
  similar = []
  for i in related[:1000]:
    b = chess.Board(i['fen'])
    # another bitwise XOR but this time more robust
    dif = len(board.pieces(chess.PAWN, True) ^ b.pieces(chess.PAWN, True))**2 + len(board.pieces(chess.PAWN, False) ^ b.pieces(chess.PAWN, False))**2
    i['difference'] = dif
    if dif < 10:
      similar.append(i)
  return similar

def recommend(pgn_string):
  pgn = StringIO(pgn_string)
  game = chess.pgn.read_game(pgn)
  node = game

  boards = []
  unique_pawns = []
  while not node.is_end():
    next_node = node.variation(0)

    if node.board().fullmove_number > 7:
      pawns = {'w': node.board().pieces(chess.PAWN, True), 'b': node.board().pieces(chess.PAWN, False)}
      if pawns not in unique_pawns:
        unique_pawns.append(pawns)
        boards.append(node.board())
    node = next_node

  similar = []
  for b in boards:
    similar.extend(similar_to(puzzleColl, b))

  return sorted(similar, key=lambda x: -x['perf']['gl']['r'])


client = MongoClient()
db = client.lichess
puzzleColl = db.puzzle

#update puzzleColl for indexing
#for p in puzzleColl.find({"_id": {"$gt": 61000}}):
#  update_structures(puzzleColl, p)

# game we're finding related puzzles to
pgn_string = """
[Event "Rated game"]
[Site "https://lichess.org/dUK8cpPA"]
[Date "2017.01.14"]
[White "thibault"]
[Black "Paul-G"]
[Result "1-0"]
[WhiteElo "1763"]
[BlackElo "1569"]
[PlyCount "93"]
[Variant "Standard"]
[TimeControl "180+2"]
[ECO "C30"]
[Opening "King's Gambit"]
[Termination "Normal"]
[Annotator "lichess.org"]

1. e4 e5 2. f4?! { (0.31  -0.54) Inaccuracy. Best move was Nf3. } { C30 King's Gambit } (2. Nf3 Nf6 3. Nxe5 d6 4. Nf3 Nxe4 5. d3 Nf6 6. Nc3 Nc6 7. d4 Be7 8. Bd3 O-O) 2... d6?! { (-0.54  0.03) Inaccuracy. Best move was exf4. } (2... exf4 3. Qe2 Nc6 4. Nf3 g5 5. h3 d6 6. d4 Bg7 7. d5 Ne5 8. Nbd2 Nxf3+ 9. Qxf3) 3. Nf3 Nc6?! { (-0.40  0.37) Inaccuracy. Best move was exf4. } (3... exf4) 4. Bc4 Bg4 5. O-O Nf6 6. h3 Bxf3 7. Qxf3 Nd4 8. Qd3 Be7 9. Nc3?! { (0.49  -0.09) Inaccuracy. Best move was c3. } (9. c3 Ne6 10. fxe5 dxe5 11. Qg3 Qd6 12. d3 Nh5 13. Qg4 Nf6 14. Qf3 c6 15. Be3 O-O) 9... a6 10. Nd5?! { (0.03  -0.72) Inaccuracy. Best move was Ne2. } (10. Ne2 b5) 10... Nxd5? { (-0.72  0.93) Mistake. Best move was b5. } (10... b5) 11. Bxd5 c6? { (0.95  2.35) Mistake. Best move was O-O. } (11... O-O) 12. Bxf7+ Kxf7 13. fxe5+ Ke8 14. Qxd4 dxe5 15. Qxe5 Qb6+?? { (2.47  6.00) Blunder. Best move was Rf8. } (15... Rf8 16. d4 Qd6 17. Rxf8+ Kxf8 18. Qxd6 Bxd6 19. Be3 Ke7 20. Kf2 Rf8+ 21. Ke2 a5 22. Rf1) 16. d4 Rd8 17. Bg5?? { (5.10  0.28) Blunder. Best move was Bh6. } (17. Bh6 Kd7) 17... Qxd4+ 18. Qxd4 Rxd4 19. Bxe7 Kxe7 20. Rae1 Rd2 21. Rf2 Rxf2 22. Kxf2 Rf8+ 23. Ke3 Ke6 24. c4 Ke5?! { (0.44  1.07) Inaccuracy. Best move was Rf6. } (24... Rf6 25. Rd1 Rg6 26. Rd2 Ke5 27. c5 h5 28. Rd7 Rxg2 29. Re7+ Kf6 30. Rxb7 Rh2 31. Kd4) 25. Rd1 Rf4 26. Rd4?! { (1.05  0.20) Inaccuracy. Best move was Rd7. } (26. Rd7 Rxe4+ 27. Kd3 Rf4 28. Rxg7 Rf2 29. Kc3 h5 30. h4 b6 31. Rg6 a5 32. Rxc6 Rxg2) 26... g6?! { (0.20  1.04) Inaccuracy. Best move was Rf2. } (26... Rf2) 27. g3? { (1.04  0.00) Mistake. Best move was Rd7. } (27. Rd7 Rxe4+ 28. Kd3 Rf4 29. Rxb7 Rf2 30. Re7+ Kf6 31. Re2 Rxe2 32. Kxe2 Ke5 33. Kd3 c5) 27... Rf1?! { (0.00  0.70) Inaccuracy. Best move was Rf2. } (27... Rf2 28. Rd7 Rxb2 29. Re7+ Kd6 30. Rxh7 a5 31. h4 a4 32. a3 Ke5 33. Re7+ Kf6 34. Rd7) 28. Rd7 Re1+ 29. Kf2 Rxe4 30. Rxh7 Rxc4 31. Rxb7 Rc2+ 32. Kf3 Rd2 33. a4 Rd3+ 34. Kg4 Rd4+?! { (1.51  2.47) Inaccuracy. Best move was Kf6. } (34... Kf6 35. a5 Rd4+ 36. Kf3 Ra4 37. b4 c5 38. bxc5 Rxa5 39. Rb6+ Ke7 40. Rxg6 Rxc5 41. Rxa6) 35. Kg5 Rxa4 36. Kxg6 Ra5? { (2.15  4.88) Mistake. Best move was a5. } (36... a5 37. g4) 37. Rf7? { (4.88  2.89) Mistake. Best move was h4. } (37. h4 Ra4 38. Kg5 Ra5 39. h5 Ke6+ 40. Kg6 Ra4 41. b4 a5 42. h6 Ra3 43. g4 axb4) 37... Rb5?? { (2.89  45.83) Blunder. Best move was Ra4. } (37... Ra4 38. Rf5+) 38. Rf5+ Ke6?! { (13.92  Mate in 22) Checkmate is now unavoidable. Best move was Ke4. } (38... Ke4 39. Rxb5) 39. Rxb5 axb5?! { (114.47  Mate in 17) Checkmate is now unavoidable. Best move was Kd6. } (39... Kd6 40. h4) 40. h4 c5 41. h5 Ke7 42. h6 Kf8 43. Kf5 c4 44. Ke4 Kg8 45. Kd4 Kh7 46. Kc5 Kxh6 47. Kxb5 { Black resigns } 1-0
"""

pprint.pprint(recommend(pgn_string))