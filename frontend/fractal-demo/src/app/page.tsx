import { FractalViewer } from '@/components/fractal/FractalViewer'

export default function HomePage() {
  return (
    <main className="w-full h-screen">
      <FractalViewer
        initialCenter={{ x: 0, y: 0 }}
        initialScale={1.0}
        enablePredictive={true}
        debugMode={false}
      />
    </main>
  )
}