import { ConfirmDialog } from '@/components/confirm-dialog'
import { useLocation, useNavigate } from 'react-router-dom'

export function SignOutDialog({ open, onOpenChange }) {
    const navigate = useNavigate()
    const location = useLocation()
    //   const { auth } = useAuthStore()

    console.log(location)

    const handleSignOut = () => {
        // auth.reset()
        // Preserve current location for redirect after sign-in
        const currentPath = location.pathname
        // navigate({
        //   to: '/sign-in',
        //   search: { redirect: currentPath },
        //   replace: true,
        // })
        navigate(`/sign-in?redirect=${encodeURIComponent(currentPath)}`, {
            replace: true,
        })
    }

    return (
        <ConfirmDialog
            open={open}
            onOpenChange={onOpenChange}
            title='Sign out'
            desc='Are you sure you want to sign out? You will need to sign in again to access your account.'
            confirmText='Sign out'
            destructive
            handleConfirm={handleSignOut}
            className='sm:max-w-sm'
        />
    )
}
