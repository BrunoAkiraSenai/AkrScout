import { useSEO } from './hooks/useSEO'
import { AppRoutes } from './routes'

export default function App() {
  useSEO()
  return <AppRoutes />
}
