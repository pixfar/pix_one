import { useState } from "react"

export default function useDialogState(
    initialState = null
) {
    const [open, _setOpen] = useState(initialState)

    const setOpen = (str) =>
        _setOpen((prev) => (prev === str ? null : str))

    return [open, setOpen]
}