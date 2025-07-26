type HeaderProps = {
	title: string;
};
const Header: React.FC<HeaderProps> = ({ title }) => {
	return (
		<div className='bg-gradient-to-r from-blue-600 to-purple-600 p-8 text-center'>
			<div className='flex flex-row align-middle justify-center gap-4'>
				<div className='w-16 h-16 my-auto rounded-full border-dashed border border-white '>
					<img
						src='logo.png'
						alt='Logo'
						className='p-3 brightness-200 contrast-200 invert'
					/>
				</div>

				<h1 className='text-3xl font-bold text-white my-auto'>{title}</h1>
			</div>
		</div>
	);
};
export default Header;
