import React from 'react';
import Signin from './Signin/Signin';
import Signup from './Signup/Signup';

const Profile = () => {
  return (
    <div className='min-h-screen'>
      <Signin />
      <Signup />
    </div>
  );
};

export default Profile;
