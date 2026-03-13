export interface FiltroConfig {
  campo: string;

  label: string;

  tipo: 'checkbox' | 'radio' | 'select' | 'range';

  opcoes?: any[];
}
