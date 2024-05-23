board = [
                ["M", "M", "M", "M", "M", "M", "M", "M", "M", "M"],
                ["M", " ", " ", " ", " ", " ", " ", " ", " ", "M"],
                ["M", " ", " ", " ", " ", "3", " ", " ", " ", "M"],
                ["M", " ", " ", " ", "3", "M", " ", " ", " ", "M"],
                ["M", " ", " ", " ", " ", " ", " ", " ", " ", "M"],
                ["M", "2", " ", " ", " ", " ", " ", " ", " ", "M"],
                ["M", "2", " ", " ", " ", "M", "M", "M", "M", "M"],
                ["M", "2", " ", " ", " ", " ", " ", "M", "M", "M"],
                ["M", " ", " ", " ", " ", " ", " ", " ", " ", "M"],
                ["M", "M", "M", "M", "M", "M", "M", "M", "M", "M"],
            ]
board = Board(board)
friendlies = [TankMech((1,1), 5, 3, 3),
			  TankMech((1,2), 3, 3, 3),
			  TankMech((1,3), 2, 3, 2) 
			 ]
enemies = [Scorpion((8, 8), 3, 3, 2),
			Firefly((8,7), 2, 2, 1),
			Firefly((7,6), 1, 1, 1)
			]
entities = friendlies + enemies

model = BreachModel(board, entities)
model.end_turn()
