import { loadPyodide, PyodideInterface } from 'pyodide';
import { useEffect, useMemo, useRef, useState } from 'react';

export const usePyodide = (indexURL: string, packages?: string[]) => {
	const [pyodide, setPyodide] = useState<PyodideInterface>();
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState<unknown>(null);
	const pyodideRef = useRef<PyodideInterface>(null);

	// Memoize the packages array to ensure stability
	const stablePackages = useMemo(() => packages, [packages]);

	useEffect(() => {
		const loadPyodideInstance = async () => {
			try {
				setIsLoading(true);
				const pyodideInstance = await loadPyodide({ indexURL });
				if (stablePackages?.length) {
					await pyodideInstance.loadPackage(stablePackages);
				}
				pyodideInstance.globals.set('pyodide', pyodideInstance);
				pyodideRef.current = pyodideInstance;
				setPyodide(pyodideInstance);
			} catch (err) {
				setError(err);
			} finally {
				setIsLoading(false);
			}
		};

		loadPyodideInstance();
	}, [indexURL, stablePackages]); // Use stablePackages instead of packages

	return { pyodide, isLoading, error };
};
