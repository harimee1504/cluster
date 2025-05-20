import { lazy, Suspense } from 'react';

const RemoteComponent = lazy(() => import('auth/wrapper'!));

function App() {

  let data = {
    navMain: [
      {
        title: "TaskNote",
        url: "#",
        icon: undefined,
        isActive: true,
        items: [
          {
            title: "Todo",
            url: () => {},
          },
          {
            title: "Note",
            url: () => {},
          },
        ],
      },
    ],
  };

  return (
      <Suspense fallback={<div>Loading...</div>}>
        <RemoteComponent data={data}>
          <div className="django-child-container" id="django-child-container"></div>
        </RemoteComponent>
      </Suspense>
  )
}

export default App
