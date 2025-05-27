import { createRoot } from "react-dom/client";

const Toast = ({ message, type = "success", duration = 5000 }) => {
  return (
    <div
      className={`fixed top-4 right-4 z-50 animate-fade-in ${
        type === "error"
          ? "bg-red-100 text-red-900"
          : "bg-green-100 text-green-900"
      } rounded-lg px-4 py-3 shadow-md`}
    >
      <p>{message}</p>
    </div>
  );
};

export const showToast = (message, type = "success", duration = 5000) => {
  const container = document.createElement("div");
  document.body.appendChild(container);

  const root = createRoot(container);
  root.render(<Toast message={message} type={type} duration={duration} />);

  setTimeout(() => {
    root.unmount();
    container.remove();
  }, duration);
};

export default Toast;
