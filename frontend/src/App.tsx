import { useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="flex min-h-svh items-center justify-center bg-background p-6">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Knowledge OS</CardTitle>
          <CardDescription>
            shadcn and Vite are wired up. Click the button to test interactivity.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Count: {count}</p>
        </CardContent>
        <CardFooter>
          <Button onClick={() => setCount((value) => value + 1)}>
            Increment
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}

export default App
