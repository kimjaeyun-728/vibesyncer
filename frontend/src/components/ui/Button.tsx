import { clsx } from 'clsx';
import type { ReactNode } from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant: 'primary' | 'secondary' | 'tertiary';
}

const Button = ({ children, variant = 'primary', ...props }: ButtonProps) => {
  const baseStyle = 'w-full px-6 py-3 rounded-lg transition-colors';
  const variants = {
    primary: 'bg-indigo-500 hover:bg-indigo-600 text-white',
    secondary: 'bg-gray-600 hover:bg-gray-700 text-white',
    tertiary: 'bg-green-500 hover:bg-green-600 text-white',
  };

  return (
    <button className={clsx(baseStyle, variants[variant])} {...props}>
      {children}
    </button>
  );
};

export default Button;
