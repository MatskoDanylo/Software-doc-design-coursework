import { Link } from 'react-router-dom'
import StateMessage from '../components/StateMessage'
import { buttonOutline } from '../components/ui'

export default function PricingPage() {
  return (
    <StateMessage
      title="Преміум-підписка"
      text="До 1080p і без реклами. Оформлення підписки з’явиться найближчим часом"
      action={
        <Link to="/catalog" className={buttonOutline}>
          До каталогу
        </Link>
      }
    />
  )
}
