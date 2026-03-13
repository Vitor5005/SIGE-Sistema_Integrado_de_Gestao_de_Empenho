export interface FiltroConfig {
  campo: string;

  label: string;

  tipo: 'checkbox' | 'radio' | 'select' | 'range' | 'date-range';

  opcoes?: any[];
}
