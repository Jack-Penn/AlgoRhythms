import { useEffect } from "react";
import { testapi } from "../lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";

function Home() {
	const queryClient = useQueryClient();

	const testQuery = useQuery({ queryKey: ["test"], queryFn: testapi });

	console.log(testQuery.data);

	return (
		<div className='min-h-screen bg-gradient-to-br from-indigo-900 to-purple-800 flex flex-col items-center justify-center p-4'>
			<div className='w-full max-w-md bg-background rounded-2xl shadow-xl overflow-hidden'>
				{/* Header Section */}
				<div className='bg-gradient-to-r from-blue-600 to-purple-600 p-8 text-center'>
					<div className='flex flex-row align-middle justify-center gap-4 pb-5'>
						<div className='w-16 h-16 my-auto rounded-full border-dashed border border-white '>
							<img
								src='logo.png'
								alt='Logo'
								className='p-3 brightness-200 contrast-200 invert'
							/>
						</div>

						<h1 className='text-4xl font-bold text-white my-auto'>
							AlgoRhythms
						</h1>
					</div>
					<p className='text-blue-100 font-medium text-lg'>
						Get a playlist tailored to your mood
					</p>
				</div>

				{/* Form Section */}
				<div className='p-8'>
					<div className='space-y-5'>
						<div>
							<input
								type='text'
								className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
								placeholder='Username / Emaill'
							/>
						</div>

						<div>
							<input
								type='password'
								className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
								placeholder='Enter your password'
							/>
						</div>

						<button className='w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-3 rounded-lg hover:opacity-90 transition-opacity shadow-md'>
							Login
						</button>
					</div>

					<div className='mt-8 pt-5 border-t border-gray-200'>
						<button className='w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-3 rounded-lg hover:opacity-90 transition-opacity shadow-md'>
							Continue as Guest
						</button>
					</div>
				</div>
			</div>
		</div>
	);
}

export default Home;
