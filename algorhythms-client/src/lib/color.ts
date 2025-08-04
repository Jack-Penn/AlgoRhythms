const colorValues = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950];

export function lerpTailwindColor(
	color1: string,
	color2: string,
	value: number,
	colorSpace: string = "oklch",
) {
	return `color-mix(in ${colorSpace}, var(--color-${color1}), var(--color-${color2}) ${
		value * 100
	}%)`;
}