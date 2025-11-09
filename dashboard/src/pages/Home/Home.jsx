import Banner from "./Banner/Banner";
import BusinessPlatform from "./BusinessPlatform/BusinessPlatform";
import Services from "./Services/Services";
import Tech from "./Tech/Tech";
import Vission from "./Vission/Vission";


const Home = () => {
  return (
    <div>
      <Banner />
      <Vission />
      <Services />
      <BusinessPlatform />
      <Tech />
    </div>
  );
};

export default Home;
