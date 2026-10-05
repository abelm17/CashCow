import { useState, useEffect } from "react";
import apiClient from "../../api/client";

function AtmList( { atms }) {
    return (
        <Grid container spacing= {2}>
            {atms.map((atm) => (
                <Grid item key={atm.id}>
                    <AtmCard atm={atm}/>
                </Grid>
            ))}
        </Grid>
    );
}

export default AtmList;
