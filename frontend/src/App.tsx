import axios from 'axios';
import React from 'react';
import { usePyodide } from './usePyodide';

type GameName = 'snake_game' | 'space_invaders' | 'chess' | '2048';

function App() {
	const canvasRef = React.useRef<HTMLCanvasElement>(null);
	const packages = React.useMemo(() => ['micropip', 'pygame-ce'], []);
	const [score, setScore] = React.useState(0);
	const [isGameEnded, setIsGameEnded] = React.useState(false);
	const [speed, setSpeed] = React.useState(60);
	const [canvasSize, setCanvasSize] = React.useState(500);
	const [isGameRunning, setIsGameRunning] = React.useState(false);
	const [gameName, setGameName] = React.useState<GameName>('snake_game');

	const { pyodide, isLoading } = usePyodide(
		import.meta.env.VITE_PYODIDE_URL,
		packages
	);
	async function runGame() {
		const game = await axios.post(
			import.meta.env.VITE_BACKEND_URL + '/assets',
			{ gameName },
			{
				responseType: 'arraybuffer',
			}
		);
		const gameScript = await axios.post(
			import.meta.env.VITE_BACKEND_URL + '/code',
			{ gameName },
			{
				responseType: 'text',
			}
		);
		const gameData = game.data;
		const scriptData = gameScript.data;
		const canvas = canvasRef.current;
		if (!canvas) return;
		if (!pyodide) return;
		pyodide.globals.set('pyodide', pyodide);
		pyodide.globals.set('canvas', canvas);
		pyodide.globals.set('speed', speed);
		pyodide.globals.set('setScore', setScore);
		pyodide.globals.set('setIsGameEnded', setIsGameEnded);
		pyodide.canvas.setCanvas2D(canvas);
		pyodide.unpackArchive(gameData, 'zip');
		pyodide.runPythonAsync(scriptData);
		setIsGameRunning(true);
	}

	return (
		<>
			<div className="flex flex-col items-center justify-center h-screen gap-8">
				<h1 className="text-3xl font-bold text-center">Game with Pyodide</h1>
				<div>
					<select
						className="w-full px-2 py-1"
						onChange={(e) => setGameName(e.target.value as GameName)}
						disabled={isGameRunning}
					>
						<option value="snake_game">Snake Game</option>
						<option value="space_invaders">Space Invaders</option>
						<option value="chess">Chess</option>
						<option value="2048">2048</option>
					</select>
				</div>
				<div className="flex items-center justify-center gap-4">
					<button
						className="w-full px-4 py-2 font-bold text-white bg-blue-500 rounded hover:bg-blue-700 disabled:bg-gray-400"
						onClick={runGame}
						disabled={isLoading || isGameRunning}
					>
						Run Game
					</button>
					<div className="w-full">
						<div className="text-center">
							<p className="text-xl font-bold">Score: {score}</p>
						</div>
						<div className="text-center">
							<p className="text-xl font-bold whitespace-nowrap">
								Is Game Ended: {isGameEnded ? 'Yes' : 'No'}
							</p>
						</div>
					</div>
					<div>
						<p className="text-xl font-bold">Speed:{speed}</p>
						<div className="flex gap-2">
							<button
								className="px-4 py-2 font-bold text-white bg-blue-500 rounded hover:bg-blue-700 disabled:bg-gray-400"
								onClick={() => {
									setSpeed((prevSpeed) => prevSpeed + 5);
								}}
								disabled={isGameRunning}
							>
								+
							</button>
							<button
								className="px-4 py-2 font-bold text-white bg-blue-500 rounded hover:bg-blue-700 disabled:bg-gray-400"
								onClick={() => {
									setSpeed((prevSpeed) => prevSpeed - 5);
								}}
								disabled={isGameRunning}
							>
								-
							</button>
						</div>
					</div>
				</div>
				<canvas
					id="canvas"
					width={canvasSize}
					height={canvasSize}
					ref={canvasRef}
					className="border-2 border-black rounded-md"
				></canvas>
				<div className="flex flex-col items-center justify-center gap-4">
					<p className="text-xl font-bold">Canvas Size: {canvasSize}</p>
					<div className="flex gap-2">
						<button
							className="px-4 py-2 font-bold text-white bg-blue-500 rounded hover:bg-blue-700 disabled:bg-gray-400"
							onClick={() => {
								setCanvasSize((prevCanvasSize) => prevCanvasSize + 50);
							}}
							disabled={isGameRunning}
						>
							+
						</button>
						<button
							className="px-4 py-2 font-bold text-white bg-blue-500 rounded hover:bg-blue-700 disabled:bg-gray-400"
							onClick={() => {
								setCanvasSize((prevCanvasSize) => prevCanvasSize - 50);
							}}
							disabled={isGameRunning}
						>
							-
						</button>
					</div>
				</div>
			</div>
		</>
	);
}

export default App;
