import { useEffect, useState } from 'react'

// PyWebView API types are now in @/lib/pywebview.ts

function App() {
  const [bridgeReady, setBridgeReady] = useState(false)
  const [apiResponse, setApiResponse] = useState<string | null>(null)

  useEffect(() => {
    /**
     * Listen for pywebviewready event
     *
     * This event fires when PyWebView has finished setting up the JS bridge.
     * Only after this event can we safely call window.pywebview.api methods.
     */
    const handlePyWebViewReady = () => {
      console.log('[DiscordOpus] PyWebView bridge ready')
      setBridgeReady(true)

      // Test the bridge with a ping
      if (window.pywebview?.api) {
        window.pywebview.api.ping().then((response) => {
          console.log('[DiscordOpus] Ping response:', response)
          setApiResponse(response)
        })
      }
    }

    // Check if already ready (can happen if event fired before React mounted)
    if (window.pywebview) {
      handlePyWebViewReady()
    } else {
      // Wait for the event
      window.addEventListener('pywebviewready', handlePyWebViewReady)
    }

    return () => {
      window.removeEventListener('pywebviewready', handlePyWebViewReady)
    }
  }, [])

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">DiscordOpus</h1>
        <p className="text-gray-400 mb-2">Loading...</p>

        {/* Bridge status indicator */}
        <div className="mt-8 text-sm text-gray-500">
          {bridgeReady ? (
            <span className="text-green-500">
              Bridge connected {apiResponse && `(${apiResponse})`}
            </span>
          ) : (
            <span className="text-yellow-500">
              Waiting for PyWebView bridge...
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
